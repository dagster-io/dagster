from dagster import check

from dagster.core.definitions import Result, Solid, OutputDefinition

from dagster.core.materializable import Materializeable

from .objects import (
    ExecutionPlanInfo,
    ExecutionStep,
    ExecutionSubPlan,
    StepInput,
    StepOutput,
    StepOutputHandle,
    StepTag,
)

from .utility import create_join_step

MATERIALIZATION_THUNK_INPUT = 'materialization_thunk_input'
MATERIALIZATION_THUNK_OUTPUT = 'materialization_thunk_output'


def _create_materialization_lambda(materializable, config_spec):
    check.inst_param(materializable, 'materializable', Materializeable)

    def _fn(_info, _step, inputs):
        runtime_value = inputs[MATERIALIZATION_THUNK_INPUT]
        materializable.materialize_runtime_value(config_spec, runtime_value)
        yield Result(runtime_value, MATERIALIZATION_THUNK_OUTPUT)

    return _fn


def configs_for_output(solid, solid_config, output_def):
    for output_spec in solid_config.outputs:
        check.invariant(len(output_spec) == 1)
        output_name, output_spec = list(output_spec.items())[0]
        check.invariant(solid.has_output(output_name))
        if output_name == output_def.name:
            yield output_spec


def decorate_with_output_materializations(execution_info, solid, output_def, subplan):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(subplan, 'subplan', ExecutionSubPlan)

    solid_config = execution_info.environment.solids.get(solid.name)

    if not (solid_config and solid_config.outputs):
        return subplan

    new_steps = []

    for mat_count, output_spec in enumerate(configs_for_output(solid, solid_config, output_def)):
        new_steps.append(
            ExecutionStep(
                key='{solid}.materialization.output.{output}.{mat_count}'.format(
                    solid=solid.name, output=output_def.name, mat_count=mat_count
                ),
                step_inputs=[
                    StepInput(
                        name=MATERIALIZATION_THUNK_INPUT,
                        dagster_type=output_def.dagster_type,
                        prev_output_handle=subplan.terminal_step_output_handle,
                    )
                ],
                step_outputs=[
                    StepOutput(
                        name=MATERIALIZATION_THUNK_OUTPUT, dagster_type=output_def.dagster_type
                    )
                ],
                tag=StepTag.MATERIALIZATION_THUNK,
                solid=solid,
                compute_fn=_create_materialization_lambda(output_def.dagster_type, output_spec),
            )
        )

    join_step = create_join_step(
        solid,
        '{solid}.materialization.output.{output}.join'.format(
            solid=solid.name, output=output_def.name
        ),
        new_steps,
        MATERIALIZATION_THUNK_OUTPUT,
    )

    output_name = join_step.step_outputs[0].name
    return ExecutionSubPlan(new_steps + [join_step], StepOutputHandle(join_step, output_name))
