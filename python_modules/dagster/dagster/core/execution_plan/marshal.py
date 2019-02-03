from dagster import check
from dagster.core.definitions import Result
from .objects import (
    ExecutionStep,
    StepBuilderState,
    StepInput,
    StepKind,
    StepOutput,
    StepOutputHandle,
)

UNMARSHAL_INPUT_OUTPUT = 'unmarshal-input-output'


def create_unmarshal_input_step(state, step, step_input, marshalling_key):
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(step_input, 'step_input', StepInput)
    check.str_param(marshalling_key, 'marshalling_key')

    def _compute_fn(context, _step, _inputs):
        yield Result(
            context.persistence_policy.read_value(
                step_input.runtime_type.serialization_strategy, marshalling_key
            ),
            UNMARSHAL_INPUT_OUTPUT,
        )

    return StepOutputHandle(
        ExecutionStep(
            key='{step_key}.unmarshal-input.{input_name}'.format(
                step_key=step.key, input_name=step_input.name
            ),
            step_inputs=[],
            step_outputs=[StepOutput(UNMARSHAL_INPUT_OUTPUT, step_input.runtime_type)],
            compute_fn=_compute_fn,
            kind=StepKind.UNMARSHAL_INPUT,
            solid=step.solid,
            tags=state.get_tags(),
        ),
        UNMARSHAL_INPUT_OUTPUT,
    )


MARSHAL_OUTPUT_INPUT = 'marshal-output-input'


def create_marshal_output_step(state, step, step_output, marshalling_key):
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(step_output, 'step_output', StepOutput)
    check.str_param(marshalling_key, 'marshalling_key')

    def _compute_fn(context, _step, inputs):
        context.persistence_policy.write_value(
            step_output.runtime_type.serialization_strategy,
            marshalling_key,
            inputs[MARSHAL_OUTPUT_INPUT],
        )

    return ExecutionStep(
        key='{step_key}.marshal-output.{output_name}'.format(
            step_key=step.key, output_name=step_output.name
        ),
        step_inputs=[
            StepInput(
                MARSHAL_OUTPUT_INPUT,
                step_output.runtime_type,
                StepOutputHandle(step, step_output.name),
            )
        ],
        step_outputs=[],
        compute_fn=_compute_fn,
        kind=StepKind.MARSHAL_OUTPUT,
        solid=step.solid,
        tags=state.get_tags(),
    )
