from dagster import check
from dagster.core.definitions import (
    ExpectationResult,
    Materialization,
    PipelineDefinition,
    Result,
    Solid,
    SolidHandle,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution_context import SystemTransformExecutionContext
from dagster.core.user_context import TransformExecutionContext

from .objects import ExecutionStep, StepInput, StepKind, StepOutput, StepOutputValue


def create_transform_step(pipeline_def, environment_config, solid, step_inputs):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)

    return ExecutionStep(
        pipeline_name=pipeline_def.name,
        key_suffix='transform',
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(
                name=name, runtime_type=output_def.runtime_type, optional=output_def.optional
            )
            for name, output_def in solid.definition.output_dict.items()
        ],
        compute_fn=lambda step_context, inputs: _execute_core_transform(
            step_context.for_transform(), inputs, solid.definition.transform_fn
        ),
        kind=StepKind.TRANSFORM,
        solid_handle=SolidHandle(solid.name, solid.definition.name),
        metadata=solid.step_metadata_fn(environment_config) if solid.step_metadata_fn else {},
    )


def _yield_transform_results(transform_context, inputs, transform_fn):
    check.inst_param(transform_context, 'transform_context', SystemTransformExecutionContext)
    step = transform_context.step
    gen = transform_fn(TransformExecutionContext(transform_context), inputs)

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than '
                'yielding it. The transform_fn of the core SolidDefinition must yield '
                'its results'
            ).format(solid_name=step.solid_handle.name)
        )

    if gen is None:
        return

    for result in gen:
        if isinstance(result, Result):
            transform_context.log.info(
                'Solid {solid} emitted output "{output}" value {value}'.format(
                    solid=step.solid_handle.name,
                    output=result.output_name,
                    value=repr(result.value),
                )
            )
            yield StepOutputValue(output_name=result.output_name, value=result.value)

        elif isinstance(result, (Materialization, ExpectationResult)):
            yield result

        else:
            raise DagsterInvariantViolationError(
                (
                    'Transform for solid {solid_name} yielded {result} rather an '
                    'an instance of the Result or Materialization class.'
                ).format(result=repr(result), solid_name=step.solid_handle.name)
            )


def _execute_core_transform(transform_context, inputs, transform_fn):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(transform_context, 'transform_context', SystemTransformExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)

    step = transform_context.step

    transform_context.log.debug(
        'Executing core transform for solid {solid}.'.format(solid=step.solid_handle.name)
    )

    all_results = []
    for step_output in _yield_transform_results(transform_context, inputs, transform_fn):
        yield step_output
        if isinstance(step_output, StepOutputValue):
            all_results.append(step_output)

    if len(all_results) != len(step.step_outputs):
        emitted_result_names = {r.output_name for r in all_results}
        solid_output_names = {output.name for output in step.step_outputs}
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        transform_context.log.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=step.solid_handle.name, outputs=repr(omitted_outputs)
            )
        )
