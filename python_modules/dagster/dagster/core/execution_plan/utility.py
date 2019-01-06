from dagster import check
from dagster.core.definitions import Result, Solid

from .objects import (
    ExecutionValueSubPlan,
    ExecutionStep,
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
    seen_runtime_type = None
    for prev_step in prev_steps:
        prev_step_output = prev_step.step_output_named(prev_output_name)

        if seen_runtime_type is None:
            seen_runtime_type = prev_step_output.runtime_type
        else:
            check.invariant(seen_runtime_type == prev_step_output.runtime_type)

        output_handle = StepOutputHandle(prev_step, prev_output_name)

        step_inputs.append(StepInput(prev_step.key, prev_step_output.runtime_type, output_handle))

    return ExecutionStep(
        key=step_key,
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_runtime_type)],
        compute_fn=__join_lambda,
        tag=StepTag.JOIN,
        solid=solid,
    )


def create_joining_subplan(solid, join_step_key, parallel_steps, parallel_step_output):
    '''
    This captures a common pattern of fanning out a single value to N steps,
    where each step has similar structure. The strict requirement here is that each step
    must provide an output named the parameters parallel_step_output.

    This takes those steps and then uses a join node to coalesce them so that downstream
    steps can depend on a single output.

    Currently the join step just does a passthrough with no computation. It remains
    to be seen if there should be any work or verification done in this step, especially
    in multi-process environments that require marshalling between steps.
    '''
    check.inst_param(solid, 'solid', Solid)
    check.str_param(join_step_key, 'join_step_key')
    check.list_param(parallel_steps, 'parallel_steps', of_type=ExecutionStep)
    check.str_param(parallel_step_output, 'parallel_step_output')

    for parallel_step in parallel_steps:
        check.invariant(parallel_step.has_step_output(parallel_step_output))

    join_step = create_join_step(solid, join_step_key, parallel_steps, parallel_step_output)

    output_name = join_step.step_outputs[0].name
    return ExecutionValueSubPlan(
        parallel_steps + [join_step], StepOutputHandle(join_step, output_name)
    )


VALUE_OUTPUT = 'value_output'


def create_value_thunk_step(solid, runtime_type, step_key, value):
    def _fn(_context, _step, _inputs):
        yield Result(value, VALUE_OUTPUT)

    return StepOutputHandle(
        ExecutionStep(
            key=step_key,
            step_inputs=[],
            step_outputs=[StepOutput(VALUE_OUTPUT, runtime_type)],
            compute_fn=_fn,
            tag=StepTag.VALUE_THUNK,
            solid=solid,
        ),
        VALUE_OUTPUT,
    )
