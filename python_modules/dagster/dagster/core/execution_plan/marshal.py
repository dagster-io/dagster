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


def create_unmarshal_step(state, step, step_input, key):
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(step, 'step', ExecutionStep)
    check.inst_param(step_input, 'step_input', StepInput)
    check.str_param(key, 'key')

    def _compute_fn(context, _step, _inputs):
        input_value = context.persistence_policy.read_value(
            step_input.runtime_type.serialization_strategy, key
        )

        yield Result(input_value, UNMARSHAL_INPUT_OUTPUT)

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
