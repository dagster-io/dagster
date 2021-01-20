from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.serdes import whitelist_for_serdes
from dagster.utils import merge_dicts

from .handle import ResolvedFromDynamicStepHandle, StepHandle, UnresolvedStepHandle
from .inputs import StepInput, UnresolvedStepInput
from .outputs import StepOutput


@whitelist_for_serdes
class StepKind(Enum):
    COMPUTE = "COMPUTE"
    UNRESOLVED = "UNRESOLVED"


def is_executable_step(step):
    # This function is set up defensively to ensure new step types handled properly
    if isinstance(step, ExecutionStep):
        return True
    elif isinstance(step, UnresolvedExecutionStep):
        return False
    else:
        check.failed(f"Unexpected execution step type {step}")


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
            handle=check.inst_param(handle, "handle", (StepHandle, ResolvedFromDynamicStepHandle)),
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

    def get_mapping_key(self):
        if isinstance(self.handle, ResolvedFromDynamicStepHandle):
            return self.handle.mapping_key

        return None


class UnresolvedExecutionStep(
    namedtuple(
        "_UnresolvedExecutionStep", "handle solid step_input_dict step_output_dict pipeline_name"
    )
):
    def __new__(cls, handle, solid, step_inputs, step_outputs, pipeline_name):
        return super(UnresolvedExecutionStep, cls).__new__(
            cls,
            handle=check.inst_param(handle, "handle", UnresolvedStepHandle),
            solid=solid,
            step_input_dict={
                si.name: si
                for si in check.list_param(
                    step_inputs, "step_inputs", of_type=(StepInput, UnresolvedStepInput)
                )
            },
            step_output_dict={
                so.name: so
                for so in check.list_param(step_outputs, "step_outputs", of_type=StepOutput)
            },
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
        )

    @property
    def solid_handle(self):
        return self.handle.solid_handle

    @property
    def key(self):
        return self.handle.to_key()

    @property
    def kind(self):
        return StepKind.UNRESOLVED

    @property
    def tags(self):
        return self.solid.tags

    @property
    def step_outputs(self):
        return list(self.step_output_dict.values())

    @property
    def step_inputs(self):
        return list(self.step_input_dict.values())

    def step_output_named(self, name):
        check.str_param(name, "name")
        return self.step_output_dict[name]

    def get_all_dependency_keys(self):
        deps = set()
        for inp in self.step_inputs:
            if isinstance(inp, StepInput):
                deps.update(
                    [handle.step_key for handle in inp.get_step_output_handle_dependencies()]
                )
            elif isinstance(inp, UnresolvedStepInput):
                deps.update(
                    [
                        handle.step_key
                        for handle in inp.get_step_output_handle_deps_with_placeholders()
                    ]
                )
            else:
                check.failed(f"Unexpected step input type {inp}")

        return deps

    @property
    def resolved_by_step_key(self):
        keys = set()
        for inp in self.step_inputs:
            if isinstance(inp, UnresolvedStepInput):
                keys.add(inp.resolved_by_step_key)

        check.invariant(len(keys) == 1, "Unresolved step expects one and only one dynamic step key")

        return list(keys)[0]

    @property
    def resolved_by_output_name(self):
        keys = set()
        for inp in self.step_inputs:
            if isinstance(inp, UnresolvedStepInput):
                keys.add(inp.resolved_by_output_name)

        check.invariant(
            len(keys) == 1, "Unresolved step expects one and only one dynamic output name"
        )

        return list(keys)[0]

    def resolve(self, resolved_by_step_key, mappings):
        from .compute import _execute_core_compute

        check.invariant(
            self.resolved_by_step_key == resolved_by_step_key,
            "resolving dynamic output step key did not match",
        )

        execution_steps = []
        solid = self.solid

        for output_name, mapped_keys in mappings.items():
            if self.resolved_by_output_name != output_name:
                continue

            for mapped_key in mapped_keys:
                # handle output_name alignment
                resolved_inputs = [_resolved_input(inp, mapped_key) for inp in self.step_inputs]

                execution_steps.append(
                    ExecutionStep(
                        handle=ResolvedFromDynamicStepHandle(self.handle.solid_handle, mapped_key),
                        pipeline_name=self.pipeline_name,
                        step_inputs=resolved_inputs,
                        step_outputs=self.step_outputs,
                        compute_fn=lambda step_context, inputs: _execute_core_compute(
                            step_context.for_compute(), inputs, solid.definition.compute_fn
                        ),
                        solid=solid,
                    )
                )

        return execution_steps


def _resolved_input(step_input, map_key):
    if isinstance(step_input, StepInput):
        return step_input
    return step_input.resolve(map_key)
