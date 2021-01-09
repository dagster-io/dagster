import hashlib
from abc import ABC, abstractmethod
from collections import namedtuple

from dagster import check
from dagster.core.definitions import Failure, RetryRequested
from dagster.core.definitions.events import (
    AssetStoreOperation,
    AssetStoreOperationType,
    ObjectStoreOperation,
)
from dagster.core.definitions.input import InputDefinition
from dagster.core.errors import (
    DagsterExecutionLoadInputError,
    DagsterTypeLoadingError,
    user_code_error_boundary,
)
from dagster.core.storage.input_manager import InputManager
from dagster.serdes import whitelist_for_serdes

from .objects import TypeCheckData
from .utils import build_resources_for_manager


@whitelist_for_serdes
class StepInputData(namedtuple("_StepInputData", "input_name type_check_data")):
    """"Serializable payload of information for the result of processing a step input"""

    def __new__(cls, input_name, type_check_data):
        return super(StepInputData, cls).__new__(
            cls,
            input_name=check.str_param(input_name, "input_name"),
            type_check_data=check.opt_inst_param(type_check_data, "type_check_data", TypeCheckData),
        )


class StepInput(namedtuple("_StepInput", "name dagster_type source")):
    """Holds information for how to prepare an input for an ExecutionStep"""

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

    def get_step_output_handle_dependencies(self):
        return self.source.step_output_handle_dependencies


def join_and_hash(*args):
    lst = [check.opt_str_param(elem, "elem") for elem in args]
    if None in lst:
        return None
    else:
        unhashed = "".join(sorted(lst))
        return hashlib.sha1(unhashed.encode("utf-8")).hexdigest()


class FanInStepInputValuesWrapper(list):
    """Wrapper to distinguish fan-in input loads from values loads of a regular list"""


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

    @abstractmethod
    def can_load_input_object(self, step_context):
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
            self.input_def.name,
            self.config_data,
            metadata=self.input_def.metadata,
            dagster_type=self.input_def.dagster_type,
            resource_config=step_context.environment_config.resources[
                self.input_def.manager_key
            ].get("config", {}),
            resources=build_resources_for_manager(self.input_def.manager_key, step_context),
        )
        return _load_input_with_input_manager(loader, load_input_context)

    def compute_version(self, step_versions):
        # TODO: support versioning for root loaders
        return None

    def required_resource_keys(self):
        return {self.input_def.manager_key}

    def can_load_input_object(self, step_context):
        return True


class FromStepOutput(
    namedtuple("_FromStepOutput", "step_output_handle input_def config_data fan_in"),
    StepInputSource,
):
    """This step input source is the output of a previous step"""

    def __new__(cls, step_output_handle, input_def, config_data, fan_in):
        from .outputs import StepOutputHandle

        return super(FromStepOutput, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            input_def=check.inst_param(input_def, "input_def", InputDefinition),
            config_data=config_data,
            fan_in=check.bool_param(fan_in, "fan_in"),
        )

    def _input_dagster_type(self):
        if self.fan_in:
            return self.input_def.dagster_type.get_inner_type_for_fan_in()
        else:
            return self.input_def.dagster_type

    @property
    def step_key_dependencies(self):
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self):
        return [self.step_output_handle]

    def can_load_input_object(self, step_context):
        source_handle = self.step_output_handle
        if step_context.using_io_manager(source_handle):
            # asset store does not have a has check so assume present
            return True
        if self.input_def.manager_key:
            return True

        return step_context.intermediate_storage.has_intermediate(
            context=step_context, step_output_handle=source_handle,
        )

    def get_load_context(self, step_context):
        resource_config = (
            step_context.environment_config.resources[self.input_def.manager_key].get("config", {})
            if self.input_def.manager_key
            else None
        )
        resources = (
            build_resources_for_manager(self.input_def.manager_key, step_context)
            if self.input_def.manager_key
            else None
        )

        return step_context.for_input_manager(
            self.input_def.name,
            self.config_data,
            self.input_def.metadata,
            self.input_def.dagster_type,
            self.step_output_handle,
            resource_config,
            resources,
        )

    def load_input_object(self, step_context):
        source_handle = self.step_output_handle
        if self.input_def.manager_key:
            loader = getattr(step_context.resources, self.input_def.manager_key)
            return _load_input_with_input_manager(loader, self.get_load_context(step_context))

        io_manager = step_context.get_output_manager(source_handle)

        check.invariant(
            isinstance(io_manager, InputManager),
            f'Input "{self.input_def.name}" for step "{step_context.step.key}" is depending on '
            f'the manager of upstream output "{source_handle.output_name}" from step '
            f'"{source_handle.step_key}" to load it, but that manager is not an InputManager. '
            f"Please ensure that the resource returned for resource key "
            f'"{step_context.execution_plan.get_manager_key(source_handle)}" is an InputManager.',
        )

        obj = _load_input_with_input_manager(io_manager, self.get_load_context(step_context))

        output_def = step_context.execution_plan.get_step_output(source_handle).output_def

        # TODO yuhan retire ObjectStoreOperation https://github.com/dagster-io/dagster/issues/3043
        if isinstance(obj, ObjectStoreOperation):
            return obj
        else:
            from dagster.core.storage.asset_store import AssetStoreHandle

            return AssetStoreOperation(
                AssetStoreOperationType.GET_ASSET,
                source_handle,
                AssetStoreHandle(output_def.manager_key, output_def.metadata),
                obj=obj,
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

    def can_load_input_object(self, step_context):
        return True

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

    def can_load_input_object(self, step_context):
        return True

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

    def can_load_input_object(self, step_context):
        return any([source.can_load_input_object(step_context) for source in self.sources])

    def load_input_object(self, step_context):
        values = []
        for inner_source in self.sources:
            # perform a can_load check since some upstream steps may have skipped, and
            # we allow fan-in to continue in their absence
            if inner_source.can_load_input_object(step_context):
                values.append(inner_source.load_input_object(step_context))

        # When we're using an object store-backed intermediate store, we wrap the
        # representing the fan-in values in a FanInStepInputValuesWrapper
        # so we can yield the relevant object store events and unpack the values in the caller
        return FanInStepInputValuesWrapper(values)

    def required_resource_keys(self):
        resource_keys = set()
        for source in self.sources:
            resource_keys = resource_keys.union(source.required_resource_keys())
        return resource_keys

    def compute_version(self, step_versions):
        return join_and_hash(
            *[inner_source.compute_version(step_versions) for inner_source in self.sources]
        )


def _load_input_with_input_manager(input_manager, context):
    with user_code_error_boundary(
        DagsterExecutionLoadInputError,
        control_flow_exceptions=[Failure, RetryRequested],
        msg_fn=lambda: (
            f"Error occurred during the loading of a step input:"
            f'    step key: "{context.step_context.step.key}"'
            f'    input name: "{context.name}"'
        ),
        step_key=context.step_context.step.key,
        input_name=context.name,
    ):
        return input_manager.load_input(context)
