from dagster import check
from dagster.core.definitions import SolidHandle, SolidInputHandle, SolidOutputHandle, Output

from .objects import (
    ExecutionStep,
    SingleOutputStepCreationData,
    StepInput,
    StepKind,
    StepOutput,
    StepOutputHandle,
)

JOIN_OUTPUT = 'join_output'


def __merge_join(_context, inputs):
    yield Output(output_name=JOIN_OUTPUT, value=list(inputs.values()))


def __empty_join(_context, _inputs):
    yield Output(output_name=JOIN_OUTPUT, value=None)


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
