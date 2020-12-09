from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.definitions import AssetMaterialization, Materialization, OutputDefinition, Solid
from dagster.core.definitions.events import EventMetadataEntry
from dagster.core.execution.plan.inputs import StepInput
from dagster.serdes import whitelist_for_serdes
from dagster.utils import merge_dicts
from dagster.utils.error import SerializableErrorInfo

from .handle import StepHandle


@whitelist_for_serdes
class StepOutputHandle(namedtuple("_StepOutputHandle", "step_key output_name mapping_key")):
    def __new__(cls, step_key, output_name="result", mapping_key=None):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step_key=check.str_param(step_key, "step_key"),
            output_name=check.str_param(output_name, "output_name"),
            mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
        )


@whitelist_for_serdes
class StepInputData(namedtuple("_StepInputData", "input_name type_check_data")):
    def __new__(cls, input_name, type_check_data):
        return super(StepInputData, cls).__new__(
            cls,
            input_name=check.str_param(input_name, "input_name"),
            type_check_data=check.opt_inst_param(type_check_data, "type_check_data", TypeCheckData),
        )


@whitelist_for_serdes
class TypeCheckData(namedtuple("_TypeCheckData", "success label description metadata_entries")):
    def __new__(cls, success, label, description=None, metadata_entries=None):
        return super(TypeCheckData, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


@whitelist_for_serdes
class UserFailureData(namedtuple("_UserFailureData", "label description metadata_entries")):
    def __new__(cls, label, description=None, metadata_entries=None):
        return super(UserFailureData, cls).__new__(
            cls,
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


@whitelist_for_serdes
class StepOutputData(
    namedtuple(
        "_StepOutputData",
        "step_output_handle intermediate_materialization type_check_data version",
    )
):
    def __new__(
        cls,
        step_output_handle,
        intermediate_materialization=None,
        type_check_data=None,
        version=None,
    ):
        return super(StepOutputData, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            intermediate_materialization=check.opt_inst_param(
                intermediate_materialization,
                "intermediate_materialization",
                (AssetMaterialization, Materialization),
            ),
            type_check_data=check.opt_inst_param(type_check_data, "type_check_data", TypeCheckData),
            version=check.opt_str_param(version, "version"),
        )

    @property
    def output_name(self):
        return self.step_output_handle.output_name


@whitelist_for_serdes
class StepFailureData(namedtuple("_StepFailureData", "error user_failure_data")):
    def __new__(cls, error, user_failure_data):
        return super(StepFailureData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            user_failure_data=check.opt_inst_param(
                user_failure_data, "user_failure_data", UserFailureData
            ),
        )


@whitelist_for_serdes
class StepRetryData(namedtuple("_StepRetryData", "error seconds_to_wait")):
    def __new__(cls, error, seconds_to_wait=None):
        return super(StepRetryData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            seconds_to_wait=check.opt_int_param(seconds_to_wait, "seconds_to_wait"),
        )


@whitelist_for_serdes
class StepSuccessData(namedtuple("_StepSuccessData", "duration_ms")):
    def __new__(cls, duration_ms):
        return super(StepSuccessData, cls).__new__(
            cls, duration_ms=check.float_param(duration_ms, "duration_ms")
        )


@whitelist_for_serdes
class StepKind(Enum):
    COMPUTE = "COMPUTE"


class StepOutput(namedtuple("_StepOutput", "output_def should_materialize")):
    def __new__(
        cls, output_def, should_materialize=None,
    ):
        return super(StepOutput, cls).__new__(
            cls,
            output_def=check.inst_param(output_def, "output_def", OutputDefinition),
            should_materialize=check.bool_param(should_materialize, "should_materialize"),
        )

    @property
    def name(self):
        return self.output_def.name


class ExecutionStep(
    namedtuple(
        "_ExecutionStep",
        ("handle pipeline_name step_input_dict step_output_dict compute_fn solid logging_tags"),
    )
):
    def __new__(
        cls, handle, pipeline_name, step_inputs, step_outputs, compute_fn, solid, logging_tags=None,
    ):
        return super(ExecutionStep, cls).__new__(
            cls,
            handle=check.inst_param(handle, "handle", StepHandle),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            step_input_dict={
                si.name: si
                for si in check.list_param(step_inputs, "step_inputs", of_type=StepInput)
            },
            step_output_dict={
                so.name: so
                for so in check.list_param(step_outputs, "step_outputs", of_type=StepOutput)
            },
            # Compute_fn is the compute function for the step.
            # Not to be confused with the compute_fn of the passed in solid.
            compute_fn=check.callable_param(compute_fn, "compute_fn"),
            solid=check.inst_param(solid, "solid", Solid),
            logging_tags=merge_dicts(
                {
                    "step_key": handle.to_key(),
                    "pipeline": pipeline_name,
                    "solid": handle.solid_handle.name,
                    "solid_definition": solid.definition.name,
                },
                check.opt_dict_param(logging_tags, "logging_tags"),
            ),
        )

    @property
    def solid_handle(self):
        return self.handle.solid_handle

    @property
    def tags(self):
        return self.solid.tags

    @property
    def hook_defs(self):
        return self.solid.hook_defs

    @property
    def key(self):
        return self.handle.to_key()

    @property
    def solid_name(self):
        return self.solid_handle.name

    @property
    def kind(self):
        return StepKind.COMPUTE

    @property
    def step_outputs(self):
        return list(self.step_output_dict.values())

    @property
    def step_inputs(self):
        return list(self.step_input_dict.values())

    def has_step_output(self, name):
        check.str_param(name, "name")
        return name in self.step_output_dict

    def step_output_named(self, name):
        check.str_param(name, "name")
        return self.step_output_dict[name]

    def has_step_input(self, name):
        check.str_param(name, "name")
        return name in self.step_input_dict

    def step_input_named(self, name):
        check.str_param(name, "name")
        return self.step_input_dict[name]

    def get_execution_dependency_keys(self):
        deps = set()
        for inp in self.step_inputs:
            deps.update(inp.dependency_keys)
        return deps
