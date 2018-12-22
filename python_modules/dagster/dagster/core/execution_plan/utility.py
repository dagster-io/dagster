from dagster import check
from dagster.core.definitions import (
    Result,
    Solid,
)

from .objects import (
    ExecutionStep,
    StepCreationInfo,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepTag,
)

JOIN_OUTPUT = 'join_output'


def __join_lambda(_context, _step, inputs):
    yield Result(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def create_join_step(solid, step_key, prev_steps, prev_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.str_param(step_key, 'step_key')
    check.list_param(prev_steps, 'prev_steps', of_type=ExecutionStep)
    check.invariant(len(prev_steps) > 0)
    check.str_param(prev_output_name, 'output_name')

    step_inputs = []
    seen_dagster_type = None
    for prev_step in prev_steps:
        prev_step_output = prev_step.step_output_named(prev_output_name)

        if seen_dagster_type is None:
            seen_dagster_type = prev_step_output.dagster_type
        else:
            check.invariant(seen_dagster_type == prev_step_output.dagster_type)

        output_handle = StepOutputHandle(step_key=prev_step.key, output_name=prev_output_name)

        step_inputs.append(StepInput(prev_step.key, prev_step_output.dagster_type, output_handle))

    return ExecutionStep(
        key=step_key,
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_dagster_type)],
        compute_fn=__join_lambda,
        tag=StepTag.JOIN,
        solid=solid,
    )


VALUE_OUTPUT = 'value_output'


def create_value_thunk_step(solid, dagster_type, step_key, value):
    def _fn(_context, _step, _inputs):
        yield Result(value, VALUE_OUTPUT)

    new_step = ExecutionStep(
        key=step_key,
        step_inputs=[],
        step_outputs=[StepOutput(VALUE_OUTPUT, dagster_type)],
        compute_fn=_fn,
        tag=StepTag.VALUE_THUNK,
        solid=solid,
    )

    return StepCreationInfo(
        new_step,
        StepOutputHandle(
            step_key=new_step.key,
            output_name=VALUE_OUTPUT,
        ),
    )
