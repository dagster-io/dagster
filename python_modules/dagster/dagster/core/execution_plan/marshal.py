from dagster import check
from dagster.core.execution_context import SystemPipelineExecutionContext
from .objects import (
    ExecutionStep,
    StepInput,
    StepKind,
    StepOutput,
    StepOutputHandle,
    StepOutputValue,
    SingleOutputStepCreationData,
)

UNMARSHAL_INPUT_OUTPUT = 'unmarshal-input-output'


def create_unmarshal_input_step(pipeline_context, step, step_input, marshalling_key):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(step_input, 'step_input', StepInput)
    check.str_param(marshalling_key, 'marshalling_key')

    def _compute_fn(step_context, _inputs):
        yield StepOutputValue(
            output_name=UNMARSHAL_INPUT_OUTPUT,
            value=step_context.persistence_strategy.read_value(
                step_input.runtime_type.serialization_strategy, marshalling_key
            ),
        )

    return SingleOutputStepCreationData(
        ExecutionStep(
            pipeline_context=pipeline_context,
            key='{step_key}.unmarshal-input.{input_name}'.format(
                step_key=step.key, input_name=step_input.name
            ),
            step_inputs=[],
            step_outputs=[StepOutput(UNMARSHAL_INPUT_OUTPUT, step_input.runtime_type)],
            compute_fn=_compute_fn,
            kind=StepKind.UNMARSHAL_INPUT,
            solid=step.solid,
            tags=step.tags,
        ),
        UNMARSHAL_INPUT_OUTPUT,
    )


MARSHAL_OUTPUT_INPUT = 'marshal-output-input'


def create_marshal_output_step(pipeline_context, step, step_output, marshalling_key):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(step_output, 'step_output', StepOutput)
    check.str_param(marshalling_key, 'marshalling_key')

    def _compute_fn(step_context, inputs):
        step_context.persistence_strategy.write_value(
            step_output.runtime_type.serialization_strategy,
            marshalling_key,
            inputs[MARSHAL_OUTPUT_INPUT],
        )

    return ExecutionStep(
        pipeline_context=pipeline_context,
        key='{step_key}.marshal-output.{output_name}'.format(
            step_key=step.key, output_name=step_output.name
        ),
        step_inputs=[
            StepInput(
                MARSHAL_OUTPUT_INPUT,
                step_output.runtime_type,
                StepOutputHandle.from_step(step, step_output.name),
            )
        ],
        step_outputs=[],
        compute_fn=_compute_fn,
        kind=StepKind.MARSHAL_OUTPUT,
        solid=step.solid,
        tags=step.tags,
    )
