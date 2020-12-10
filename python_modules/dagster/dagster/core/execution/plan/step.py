from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.serdes import whitelist_for_serdes
from dagster.utils import merge_dicts

from .handle import StepHandle
from .inputs import StepInput
from .outputs import StepOutput


@whitelist_for_serdes
class StepKind(Enum):
    COMPUTE = "COMPUTE"


class ExecutionStep(
    namedtuple(
        "_ExecutionStep",
        ("handle pipeline_name step_input_dict step_output_dict compute_fn solid logging_tags"),
    )
):
    def __new__(
        cls, handle, pipeline_name, step_inputs, step_outputs, compute_fn, solid, logging_tags=None,
    ):
        from dagster.core.definitions import Solid

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
