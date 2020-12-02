import hashlib
from abc import ABC, abstractmethod
from collections import namedtuple

from dagster import check
from dagster.core.definitions.events import (
    AssetStoreOperation,
    AssetStoreOperationType,
    ObjectStoreOperation,
)
from dagster.core.definitions.input import InputDefinition
from dagster.core.errors import DagsterTypeLoadingError, user_code_error_boundary


def join_and_hash(*args):
    lst = [check.opt_str_param(elem, "elem") for elem in args]
    if None in lst:
        return None
    else:
        unhashed = "".join(sorted(lst))
        return hashlib.sha1(unhashed.encode("utf-8")).hexdigest()


class _MISSING_ITEM_SENTINEL:
    """Marker object for noting a missing item to be filtered from a fan-in input"""


class MultipleStepOutputsListWrapper(list):
    pass


class StepInputSource(ABC):
    """How to load the data for a step input"""

    @property
    def step_key_dependencies(self):
        return set()

    @property
    def step_output_handle_dependencies(self):
        return []

    @abstractmethod
    def load_input_object(self, step_context):
        raise NotImplementedError()

    def required_resource_keys(self):
        return set()

    @abstractmethod
    def compute_version(self, step_versions):
        """See resolve_step_versions in resolve_versions.py for explanation of step_versions"""
        raise NotImplementedError()


class FromRootInputManager(
    namedtuple("_FromRootInputManager", "input_def config_data"), StepInputSource,
):
    def load_input_object(self, step_context):
        loader = getattr(step_context.resources, self.input_def.manager_key)
        load_input_context = step_context.for_input_manager(
            self.input_def.name, self.config_data, input_metadata=self.input_def.metadata
        )
        return loader.load(load_input_context)

    def compute_version(self, step_versions):
        # TODO: support versioning for root loaders
        return None

    def required_resource_keys(self):
        return {self.input_def.manager_key}


class FromStepOutput(
    namedtuple(
        "_FromStepOutput", "step_output_handle input_def check_for_missing config_data fan_in"
    ),
    StepInputSource,
):
    """This step input source is the output of a previous step"""

    def __new__(cls, step_output_handle, input_def, check_for_missing, config_data, fan_in):
        from .objects import StepOutputHandle

        return super(FromStepOutput, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            input_def=check.inst_param(input_def, "input_def", InputDefinition),
            check_for_missing=check_for_missing,
            config_data=config_data,
            fan_in=check.bool_param(fan_in, "fan_in"),
        )

    @property
    def step_key_dependencies(self):
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self):
        return [self.step_output_handle]

    def _input_dagster_type(self):
        if self.fan_in:
            return self.input_def.dagster_type.get_inner_type_for_fan_in()
        else:
            return self.input_def.dagster_type

    def load_input_object(self, step_context):
        source_handle = self.step_output_handle
        if self.input_def.manager_key:
            loader = getattr(step_context.resources, self.input_def.manager_key)
            load_context = step_context.for_input_manager(
                self.input_def.name, self.config_data, self.input_def.metadata, source_handle
            )
            return loader.load(load_context)
        if step_context.using_asset_store(source_handle):
            asset_store_handle = step_context.execution_plan.get_asset_store_handle(source_handle)
            loader = getattr(step_context.resources, asset_store_handle.asset_store_key)

            asset_store_context = step_context.for_asset_store(source_handle, asset_store_handle)
            obj = loader.get_asset(asset_store_context)

            return AssetStoreOperation(
                AssetStoreOperationType.GET_ASSET, source_handle, asset_store_handle, obj=obj,
            )
        else:
            if self.check_for_missing and not step_context.intermediate_storage.has_intermediate(
                context=step_context, step_output_handle=source_handle,
            ):
                return _MISSING_ITEM_SENTINEL

            return step_context.intermediate_storage.get_intermediate(
                context=step_context,
                step_output_handle=source_handle,
                dagster_type=self._input_dagster_type(),
            )

    def compute_version(self, step_versions):
        if (
            self.step_output_handle.step_key not in step_versions
            or not step_versions[self.step_output_handle.step_key]
        ):
            return None
        else:
            return join_and_hash(
                step_versions[self.step_output_handle.step_key], self.step_output_handle.output_name
            )

    def required_resource_keys(self):
        return {self.input_def.manager_key} if self.input_def.manager_key else set()


def _generate_error_boundary_msg_for_step_input(context, input_name):
    return lambda: """Error occurred during input loading:
    input name: "{input_name}"
    step key: "{key}"
    solid invocation: "{solid}"
    solid definition: "{solid_def}"
    """.format(
        input_name=input_name,
        key=context.step.key,
        solid_def=context.solid_def.name,
        solid=context.solid.name,
    )


class FromConfig(namedtuple("_FromConfig", "config_data dagster_type input_name"), StepInputSource):
    """This step input source is configuration to be passed to a type loader"""

    def __new__(cls, config_data, dagster_type, input_name):
        return super(FromConfig, cls).__new__(
            cls, config_data=config_data, dagster_type=dagster_type, input_name=input_name
        )

    def load_input_object(self, step_context):
        with user_code_error_boundary(
            DagsterTypeLoadingError,
            msg_fn=_generate_error_boundary_msg_for_step_input(step_context, self.input_name),
        ):
            return self.dagster_type.loader.construct_from_config_value(
                step_context, self.config_data
            )

    def required_resource_keys(self):
        return (
            self.dagster_type.loader.required_resource_keys() if self.dagster_type.loader else set()
        )

    def compute_version(self, step_versions):
        return self.dagster_type.loader.compute_loaded_input_version(self.config_data)


class FromDefaultValue(namedtuple("_FromDefaultValue", "value"), StepInputSource):
    """This step input source is the default value declared on the InputDefinition"""

    def __new__(
        cls, value,
    ):
        return super(FromDefaultValue, cls).__new__(cls, value)

    def load_input_object(self, step_context):
        return self.value

    def compute_version(self, step_versions):
        return join_and_hash(repr(self.value))


class FromMultipleSources(namedtuple("_FromMultipleSources", "sources"), StepInputSource):
    """This step input is fans-in multiple sources in to a single input. The input will receive a list."""

    def __new__(cls, sources):
        check.list_param(sources, "sources", StepInputSource)
        for source in sources:
            check.invariant(
                not isinstance(source, FromMultipleSources),
                "Can not have multiple levels of FromMultipleSources StepInputSource",
            )
        return super(FromMultipleSources, cls).__new__(cls, sources=sources)

    @property
    def step_key_dependencies(self):
        keys = set()
        for source in self.sources:
            keys.update(source.step_key_dependencies)

        return keys

    @property
    def step_output_handle_dependencies(self):
        handles = []
        for source in self.sources:
            handles.extend(source.step_output_handle_dependencies)

        return handles

    def load_input_object(self, step_context):
        values = []
        for inner_source in self.sources:
            value = inner_source.load_input_object(step_context)
            if value is not _MISSING_ITEM_SENTINEL:
                values.append(value)

        # When we're using an object store-backed intermediate store, we wrap the
        # ObjectStoreOperation[] representing the fan-in values in a MultipleStepOutputsListWrapper
        # so we can yield the relevant object store events and unpack the values in the caller
        if all((isinstance(x, ObjectStoreOperation) for x in values)):
            return MultipleStepOutputsListWrapper(values)

        if all((isinstance(x, AssetStoreOperation) for x in values)):
            return MultipleStepOutputsListWrapper(values)

        return values

    def required_resource_keys(self):
        resource_keys = set()
        for source in self.sources:
            resource_keys.union(source.required_resource_keys())
        return resource_keys

    def compute_version(self, step_versions):
        return join_and_hash(
            *[inner_source.compute_version(step_versions) for inner_source in self.sources]
        )


class StepInput(namedtuple("_StepInput", "name dagster_type source")):
    def __new__(
        cls, name, dagster_type, source,
    ):
        from dagster import DagsterType

        return super(StepInput, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type=check.inst_param(dagster_type, "dagster_type", DagsterType),
            source=check.inst_param(source, "source", StepInputSource),
        )

    @property
    def dependency_keys(self):
        return self.source.step_key_dependencies
