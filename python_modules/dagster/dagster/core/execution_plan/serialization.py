import os

from dagster import check

from dagster.core.definitions import (
    OutputDefinition,
    Result,
    Solid,
)

from .objects import (
    ExecutionPlanInfo,
    ExecutionStep,
    ExecutionSubPlan,
    StepCreationInfo,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepTag,
)

SERIALIZE_INPUT = 'serialize_input'
SERIALIZE_OUTPUT = 'serialize_output'


def decorate_with_serialization(execution_info, solid, output_def, subplan):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(subplan, 'subplan', ExecutionSubPlan)

    if execution_info.serialize_intermediates:
        serialize_step = create_serialization_step(solid, output_def, subplan)
        return ExecutionSubPlan(
            steps=subplan.steps + [serialize_step],
            terminal_step_output_handle=StepOutputHandle(
                step_key=serialize_step.key,
                output_name=SERIALIZE_OUTPUT,
            )
        )
    else:
        return subplan


def _create_serialization_lambda(solid, output_def):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    def fn(context, _step, inputs):
        value = inputs[SERIALIZE_INPUT]
        path = '/tmp/dagster/runs/{run_id}/{solid_name}/outputs/{output_name}'.format(
            run_id=context.run_id,
            solid_name=solid.name,
            output_name=output_def.name,
        )

        if not os.path.exists(path):
            os.makedirs(path)

        output_def.dagster_type.serialize_value(path, value)

        context.info('Serialized output to {path}'.format(path=path))

        yield Result(value, SERIALIZE_OUTPUT)

    return fn


def create_serialization_step(solid, output_def, prev_subplan):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(prev_subplan, 'prev_subplan', ExecutionSubPlan)

    return ExecutionStep(
        key='serialize.' + solid.name + '.' + output_def.name,
        step_inputs=[
            StepInput(
                name=SERIALIZE_INPUT,
                dagster_type=output_def.dagster_type,
                prev_output_handle=prev_subplan.terminal_step_output_handle,
            )
        ],
        step_outputs=[StepOutput(
            name=SERIALIZE_OUTPUT,
            dagster_type=output_def.dagster_type,
        )],
        compute_fn=_create_serialization_lambda(solid, output_def),
        tag=StepTag.SERIALIZE,
        solid=solid,
    )
