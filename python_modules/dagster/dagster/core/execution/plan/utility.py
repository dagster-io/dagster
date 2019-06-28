from dagster import check
from dagster.core.definitions import Solid, SolidHandle, SolidInputHandle, SolidOutputHandle, Output

from .objects import (
    ExecutionStep,
    ExecutionValueSubplan,
    SingleOutputStepCreationData,
    StepInput,
    StepKind,
    StepOutput,
    StepOutputHandle,
)

JOIN_OUTPUT = 'join_output'


def __select_first_join(_context, inputs):
    yield Output(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def __merge_join(_context, inputs):
    yield Output(output_name=JOIN_OUTPUT, value=list(inputs.values()))


def __empty_join(_context, _inputs):
    yield Output(output_name=JOIN_OUTPUT, value=None)


def create_join_step(pipeline_name, solid, key_suffix, prev_steps, prev_output_name, handle):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.str_param(key_suffix, 'key_suffix')
    check.list_param(prev_steps, 'prev_steps', of_type=ExecutionStep)
    check.invariant(len(prev_steps) > 0)
    check.str_param(prev_output_name, 'output_name')

    step_inputs = []
    seen_runtime_type = None
    seen_optionality = None
    for prev_step in prev_steps:
        prev_step_output = prev_step.step_output_named(prev_output_name)

        if seen_runtime_type is None:
            seen_runtime_type = prev_step_output.runtime_type
        else:
            check.invariant(seen_runtime_type == prev_step_output.runtime_type)

        if seen_optionality is None:
            seen_optionality = prev_step_output.optional
        else:
            check.invariant(seen_optionality == prev_step_output.optional)

        output_handle = StepOutputHandle.from_step(prev_step, prev_output_name)

        step_inputs.append(StepInput(prev_step.key, prev_step_output.runtime_type, output_handle))

    return ExecutionStep(
        pipeline_name=pipeline_name,
        key_suffix=key_suffix,
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_runtime_type, optional=seen_optionality)],
        compute_fn=__select_first_join,
        kind=StepKind.JOIN,
        solid_handle=handle,
    )


def create_joining_subplan(
    pipeline_name, solid, join_step_key, parallel_steps, parallel_step_output, handle
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
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.str_param(join_step_key, 'join_step_key')
    check.list_param(parallel_steps, 'parallel_steps', of_type=ExecutionStep)
    check.str_param(parallel_step_output, 'parallel_step_output')
    check.opt_inst_param(handle, 'handle', SolidHandle)

    for parallel_step in parallel_steps:
        check.invariant(parallel_step.has_step_output(parallel_step_output))

    join_step = create_join_step(
        pipeline_name, solid, join_step_key, parallel_steps, parallel_step_output, handle
    )

    output_name = join_step.step_outputs[0].name
    return ExecutionValueSubplan(
        parallel_steps + [join_step], StepOutputHandle.from_step(join_step, output_name)
    )


def create_join_outputs_step(
    pipeline_name, input_handle, solid_output_handles, step_output_handles, handle
):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(input_handle, 'input_handle', SolidInputHandle)
    check.list_param(solid_output_handles, 'output_handles', of_type=SolidOutputHandle)
    check.dict_param(
        step_output_handles,
        'step_output_handles',
        key_type=SolidOutputHandle,
        value_type=StepOutputHandle,
    )
    check.opt_inst_param(handle, 'handle', SolidHandle)

    step_inputs = [
        StepInput(
            "{solid_output_handle.solid.name}.{solid_output_handle.output_def.name}".format(
                solid_output_handle=solid_output_handle
            ),
            solid_output_handle.output_def.runtime_type,
            step_output_handles[solid_output_handle],
        )
        for solid_output_handle in solid_output_handles
    ]

    input_type = input_handle.input_def.runtime_type

    join = ExecutionStep(
        pipeline_name=pipeline_name,
        key_suffix='input.{name}.join'.format(name=input_handle.input_def.name),
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, input_type, optional=False)],
        compute_fn=__empty_join if input_type.is_nothing else __merge_join,
        kind=StepKind.JOIN,
        solid_handle=handle,
    )

    return SingleOutputStepCreationData(join, JOIN_OUTPUT)
