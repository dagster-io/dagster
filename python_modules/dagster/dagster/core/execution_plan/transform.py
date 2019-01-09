from dagster import check
from dagster.core.definitions import Result, Solid, TransformExecutionInfo
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution_context import RuntimeExecutionContext

from .objects import ExecutionPlanInfo, ExecutionStep, StepInput, StepOutput, StepTag


def create_transform_step(execution_info, solid, step_inputs, conf):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)

    return ExecutionStep(
        key='{solid.name}.transform'.format(solid=solid),
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(name=output_def.name, runtime_type=output_def.runtime_type)
            for output_def in solid.definition.output_defs
        ],
        compute_fn=lambda context, step, inputs: _execute_core_transform(
            execution_info, context, step, conf, inputs
        ),
        tag=StepTag.TRANSFORM,
        solid=solid,
    )


def _yield_transform_results(execution_info, context, step, conf, inputs):
    gen = step.solid.definition.transform_fn(
        TransformExecutionInfo(context, conf, step.solid, execution_info.pipeline), inputs
    )

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than '
                + 'yielding it. The transform_fn of the core SolidDefinition must yield '
                + 'its results'
            ).format(solid_name=step.solid.name)
        )

    if gen is None:
        return

    for result in gen:
        if not isinstance(result, Result):
            raise DagsterInvariantViolationError(
                (
                    'Transform for solid {solid_name} yielded {result} rather an '
                    + 'an instance of the Result class.'
                ).format(result=repr(result), solid_name=step.solid.name)
            )

        context.info(
            'Solid {solid} emitted output "{output}" value {value}'.format(
                solid=step.solid.name, output=result.output_name, value=repr(result.value)
            )
        )
        yield result


def _execute_core_transform(execution_info, context, step, conf, inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.dict_param(inputs, 'inputs', key_type=str)

    solid = step.solid

    context.debug('Executing core transform for solid {solid}.'.format(solid=solid.name))

    all_results = list(_yield_transform_results(execution_info, context, step, conf, inputs))

    if len(all_results) != len(solid.definition.output_defs):
        emitted_result_names = set([r.output_name for r in all_results])
        solid_output_names = set([output_def.name for output_def in solid.definition.output_defs])
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        context.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=solid.name, outputs=repr(omitted_outputs)
            )
        )

    return all_results
