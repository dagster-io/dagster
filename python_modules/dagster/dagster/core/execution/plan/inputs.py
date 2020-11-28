from collections import namedtuple

from dagster import check
from dagster.core.definitions.events import (
    AssetStoreOperation,
    AssetStoreOperationType,
    ObjectStoreOperation,
)
from dagster.core.errors import DagsterTypeLoadingError, user_code_error_boundary


class _MISSING_ITEM_SENTINEL:
    """Marker object for noting a missing item to be filtered from a fan-in input"""


class MultipleStepOutputsListWrapper(list):
    pass


def _get_addressable_asset(step_context, step_output_handle):
    asset_store_handle = step_context.execution_plan.get_asset_store_handle(step_output_handle)
    asset_store = step_context.get_asset_store(asset_store_handle.asset_store_key)
    asset_store_context = step_context.for_asset_store(step_output_handle, asset_store_handle)

    obj = asset_store.get_asset(asset_store_context)

    return AssetStoreOperation(
        AssetStoreOperationType.GET_ASSET, step_output_handle, asset_store_handle, obj=obj,
    )


class StepInputSource:
    """How to load the data for a step input"""

    @property
    def step_key_dependencies(self):
        return set()

    @property
    def step_output_handle_dependencies(self):
        return []

    def load_input_object(self, step_context):
        pass


class FromStepOutput(
    namedtuple("_FromStepOutput", "step_output_handle dagster_type check_for_missing"),
    StepInputSource,
):
    """This step input source is the output of a previous step"""

    def __new__(cls, step_output_handle, dagster_type, check_for_missing):
        from .objects import StepOutputHandle

        return super(FromStepOutput, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            dagster_type=dagster_type,
            check_for_missing=check_for_missing,
        )

    @property
    def step_key_dependencies(self):
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self):
        return [self.step_output_handle]

    def load_input_object(self, step_context):
        source_handle = self.step_output_handle
        if step_context.using_asset_store(source_handle):
            return _get_addressable_asset(step_context, source_handle)
        else:
            if self.check_for_missing and not step_context.intermediate_storage.has_intermediate(
                context=step_context, step_output_handle=source_handle,
            ):
                return _MISSING_ITEM_SENTINEL

            return step_context.intermediate_storage.get_intermediate(
                context=step_context,
                step_output_handle=source_handle,
                dagster_type=self.dagster_type,
            )


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


class FromDefaultValue(namedtuple("_FromDefaultValue", "value"), StepInputSource):
    """This step input source is the default value declared on the InputDefinition"""

    def __new__(
        cls, value,
    ):
        return super(FromDefaultValue, cls).__new__(cls, value)

    def load_input_object(self, step_context):
        return self.value


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
