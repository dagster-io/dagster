from dagster import check
from dagster.core.execution import SystemPipelineExecutionContext
from dagster.core.definitions import Solid
from dagster.core.types.runtime import RuntimeType

from .objects import (
    ExecutionValueSubplan,
    ExecutionStep,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepOutputValue,
    StepKind,
    SingleOutputStepCreationData,
)

JOIN_OUTPUT = 'join_output'


def __join_lambda(_context, inputs):
    yield StepOutputValue(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def create_join_step(pipeline_context, solid, step_key, prev_steps, prev_output_name):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
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

        output_handle = StepOutputHandle.from_step(prev_step, prev_output_name)

        step_inputs.append(StepInput(prev_step.key, prev_step_output.runtime_type, output_handle))

    return ExecutionStep(
        pipeline_context=pipeline_context,
        key=step_key,
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_runtime_type, optional=False)],
        compute_fn=__join_lambda,
        kind=StepKind.JOIN,
        solid=solid,
        tags={},
        # tags=pipeline_context.get_tags(),
    )


def create_joining_subplan(
    pipeline_context, solid, join_step_key, parallel_steps, parallel_step_output
):
    '''
    This captures a common pattern of fanning out a single value to N steps,
    where each step has similar structure. The strict requirement here is that each step
    must provide an output named the parameters parallel_step_output.

    This takes those steps and then uses a join node to coalesce them so that downstream
    steps can depend on a single output.

    Currently the join step just does a passthrough with no computation. It remains
    to be seen if there should be any work or verification done in this step, especially
    in multi-process environments that require persistence between steps.
    '''
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.str_param(join_step_key, 'join_step_key')
    check.list_param(parallel_steps, 'parallel_steps', of_type=ExecutionStep)
    check.str_param(parallel_step_output, 'parallel_step_output')

    for parallel_step in parallel_steps:
        check.invariant(parallel_step.has_step_output(parallel_step_output))

    join_step = create_join_step(
        pipeline_context, solid, join_step_key, parallel_steps, parallel_step_output
    )

    output_name = join_step.step_outputs[0].name
    return ExecutionValueSubplan(
        parallel_steps + [join_step], StepOutputHandle.from_step(join_step, output_name)
    )


VALUE_OUTPUT = 'value_output'


def create_value_thunk_step(pipeline_context, solid, runtime_type, step_key, value):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    check.str_param(step_key, 'step_key')

    def _fn(_context, _inputs):
        yield StepOutputValue(output_name=VALUE_OUTPUT, value=value)

    return SingleOutputStepCreationData(
        ExecutionStep(
            pipeline_context=pipeline_context,
            key=step_key,
            step_inputs=[],
            step_outputs=[StepOutput(VALUE_OUTPUT, runtime_type, optional=False)],
            compute_fn=_fn,
            kind=StepKind.VALUE_THUNK,
            solid=solid,
            tags={},
        ),
        VALUE_OUTPUT,
    )
