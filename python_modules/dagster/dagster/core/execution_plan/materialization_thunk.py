import six

from dagster import check
from dagster.core.definitions import (
    Materialization,
    OutputDefinition,
    PipelineDefinition,
    Solid,
    SolidHandle,
)

from dagster.core.errors import DagsterInvariantViolationError
from .objects import (
    ExecutionStep,
    ExecutionValueSubplan,
    StepInput,
    StepKind,
    StepOutput,
    StepOutputValue,
)

from .utility import create_joining_subplan

MATERIALIZATION_THUNK_INPUT = 'materialization_thunk_input'
MATERIALIZATION_THUNK_OUTPUT = 'materialization_thunk_output'


def _create_materialization_lambda(output_def, config_spec):
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.invariant(output_def.runtime_type.output_schema, 'Must have output schema')

    def _fn(step_context, inputs):
        runtime_value = inputs[MATERIALIZATION_THUNK_INPUT]
        path = output_def.runtime_type.output_schema.materialize_runtime_value(
            step_context, config_spec, runtime_value
        )

        if not isinstance(path, six.string_types):
            raise DagsterInvariantViolationError(
                (
                    'materialize_runtime_value on type {type_name} has returned '
                    'value {value} of type {python_type}. You must return a '
                    'string (and ideally a valid file path).'
                ).format(
                    type_name=output_def.runtime_type.name,
                    value=repr(path),
                    python_type=type(path).__name__,
                )
            )

        yield StepOutputValue(output_name=MATERIALIZATION_THUNK_OUTPUT, value=runtime_value)
        yield Materialization(
            path=path,
            description=('Materialization of {solid_name}.{output_name}').format(
                output_name=output_def.name, solid_name=step_context.solid_handle.name
            ),
        )

    return _fn


def configs_for_output(solid, solid_config, output_def):
    for output_spec in solid_config.outputs:
        check.invariant(len(output_spec) == 1)
        output_name, output_spec = list(output_spec.items())[0]
        check.invariant(solid.has_output(output_name))
        if output_name == output_def.name:
            yield output_spec


def decorate_with_output_materializations(
    pipeline_def, environment_config, solid, output_def, subplan
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(subplan, 'subplan', ExecutionValueSubplan)

    solid_config = environment_config.solids.get(solid.name)

    if not (solid_config and solid_config.outputs):
        return subplan

    new_steps = []

    for mat_count, output_spec in enumerate(configs_for_output(solid, solid_config, output_def)):
        new_steps.append(
            ExecutionStep(
                pipeline_name=pipeline_def.name,
                key_suffix='outputs.{output}.materialize.{mat_count}'.format(
                    output=output_def.name, mat_count=mat_count
                ),
                step_inputs=[
                    StepInput(
                        name=MATERIALIZATION_THUNK_INPUT,
                        runtime_type=output_def.runtime_type,
                        prev_output_handle=subplan.terminal_step_output_handle,
                    )
                ],
                step_outputs=[
                    StepOutput(
                        name=MATERIALIZATION_THUNK_OUTPUT,
                        runtime_type=output_def.runtime_type,
                        optional=output_def.optional,
                    )
                ],
                kind=StepKind.MATERIALIZATION_THUNK,
                solid_handle=SolidHandle(solid.name, solid.definition.name),
                compute_fn=_create_materialization_lambda(output_def, output_spec),
            )
        )

    return create_joining_subplan(
        pipeline_def,
        solid,
        'outputs.{output}.materialize.join'.format(output=output_def.name),
        new_steps,
        MATERIALIZATION_THUNK_OUTPUT,
    )
