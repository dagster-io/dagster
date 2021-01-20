from collections import namedtuple

from dagster import check
from dagster.core.definitions import AssetMaterialization, Materialization, OutputDefinition
from dagster.serdes import whitelist_for_serdes

from .handle import UnresolvedStepHandle
from .objects import TypeCheckData


class StepOutput(namedtuple("_StepOutput", "output_def should_materialize")):
    """Holds the information for an ExecutionStep to process its outputs"""

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


@whitelist_for_serdes
class StepOutputData(
    namedtuple(
        "_StepOutputData",
        "step_output_handle intermediate_materialization type_check_data version",
    )
):
    """Serializable payload of information for the result of processing a step output"""

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

    @property
    def mapping_key(self):
        return self.step_output_handle.mapping_key


@whitelist_for_serdes
class StepOutputHandle(namedtuple("_StepOutputHandle", "step_key output_name mapping_key")):
    """A reference to a specific output that has or will occur within the scope of an execution"""

    def __new__(cls, step_key, output_name="result", mapping_key=None):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step_key=check.str_param(step_key, "step_key"),
            output_name=check.str_param(output_name, "output_name"),
            mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
        )


class UnresolvedStepOutputHandle(
    namedtuple(
        "_UnresolvedStepOutputHandle",
        "unresolved_step_handle output_name resolved_by_step_key resolved_by_output_name",
    )
):
    """
    Placeholding that will resolve to StepOutputHandle for each mapped output once the
    upstream dynamic step has completed.
    """

    def __new__(
        cls, unresolved_step_handle, output_name, resolved_by_step_key, resolved_by_output_name
    ):
        return super(UnresolvedStepOutputHandle, cls).__new__(
            cls,
            unresolved_step_handle=check.inst_param(
                unresolved_step_handle, "unresolved_step_handle", UnresolvedStepHandle
            ),
            output_name=check.str_param(output_name, "output_name"),
            # this could be a set of resolution keys to support multiple mapping operations
            resolved_by_step_key=check.str_param(resolved_by_step_key, "resolved_by_step_key"),
            resolved_by_output_name=check.str_param(
                resolved_by_output_name, "resolved_by_output_name"
            ),
        )

    def resolve(self, map_key):
        """Return a resolved StepOutputHandle"""
        return StepOutputHandle(
            self.unresolved_step_handle.resolve(map_key).to_key(), self.output_name
        )

    def get_step_output_handle_with_placeholder(self):
        """Return a StepOutputHandle with a unresolved step key as a placeholder"""
        return StepOutputHandle(self.unresolved_step_handle.to_key(), self.output_name)
