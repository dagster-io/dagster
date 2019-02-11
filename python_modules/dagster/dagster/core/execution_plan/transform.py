from dagster import check
from dagster.core.definitions import Result, Solid
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution_context import StepExecutionContext, PipelineExecutionContext

from .objects import ExecutionStep, PlanBuilder, StepInput, StepKind, StepOutput, StepOutputValue


def create_transform_step(pipeline_context, plan_builder, solid, step_inputs):
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(plan_builder, 'plan_builder', PlanBuilder)
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)

    return ExecutionStep(
        key='{solid.name}.transform'.format(solid=solid),
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(name=output_def.name, runtime_type=output_def.runtime_type)
            for output_def in solid.definition.output_defs
        ],
        compute_fn=lambda step_context, step, inputs: _execute_core_transform(
            pipeline_context, step_context.for_transform(), step, inputs
        ),
        kind=StepKind.TRANSFORM,
        solid=solid,
        tags=plan_builder.get_tags(),
    )


def _yield_transform_results(_execution_info, step_context, step, inputs):
    check.inst_param(step_context, 'step_context', StepExecutionContext)
    gen = step.solid.definition.transform_fn(step_context, inputs)

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than '
                'yielding it. The transform_fn of the core SolidDefinition must yield '
                'its results'
            ).format(solid_name=step.solid.name)
        )

    if gen is None:
        return

    for result in gen:
        if not isinstance(result, Result):
            raise DagsterInvariantViolationError(
                (
                    'Transform for solid {solid_name} yielded {result} rather an '
                    'an instance of the Result class.'
                ).format(result=repr(result), solid_name=step.solid.name)
            )

        step_context.log.info(
            'Solid {solid} emitted output "{output}" value {value}'.format(
                solid=step.solid.name, output=result.output_name, value=repr(result.value)
            )
        )
        yield StepOutputValue(output_name=result.output_name, value=result.value)


def _execute_core_transform(pipeline_context, step_context, step, inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(step_context, 'step_context', StepExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.dict_param(inputs, 'inputs', key_type=str)

    solid = step.solid

    step_context.log.debug('Executing core transform for solid {solid}.'.format(solid=solid.name))

    all_results = list(_yield_transform_results(pipeline_context, step_context, step, inputs))

    if len(all_results) != len(solid.definition.output_defs):
        emitted_result_names = {r.output_name for r in all_results}
        solid_output_names = {output_def.name for output_def in solid.definition.output_defs}
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        step_context.log.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=solid.name, outputs=repr(omitted_outputs)
            )
        )

    return all_results
