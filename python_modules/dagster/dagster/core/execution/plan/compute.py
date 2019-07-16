from dagster import check
from dagster.core.definitions import ExpectationResult, Materialization, Output, Solid, SolidHandle
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.context.system import SystemComputeExecutionContext
from dagster.core.execution.context.compute import ComputeExecutionContext

from .objects import ExecutionStep, StepInput, StepKind, StepOutput


def create_compute_step(pipeline_name, environment_config, solid, step_inputs, handle):
    check.str_param(pipeline_name, 'pipeline_name')
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)
    check.opt_inst_param(handle, 'handle', SolidHandle)

    return ExecutionStep(
        pipeline_name=pipeline_name,
        key_suffix='compute',
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(
                name=name, runtime_type=output_def.runtime_type, optional=output_def.optional
            )
            for name, output_def in solid.definition.output_dict.items()
        ],
        compute_fn=lambda step_context, inputs: _execute_core_compute(
            step_context.for_compute(), inputs, solid.definition.compute_fn
        ),
        kind=StepKind.COMPUTE,
        solid_handle=handle,
        metadata=solid.step_metadata_fn(environment_config) if solid.step_metadata_fn else {},
    )


def _yield_compute_results(compute_context, inputs, compute_fn):
    check.inst_param(compute_context, 'compute_context', SystemComputeExecutionContext)
    step = compute_context.step
    gen = compute_fn(ComputeExecutionContext(compute_context), inputs)

    if isinstance(gen, Output):
        raise DagsterInvariantViolationError(
            (
                'Compute function for solid {solid_name} returned a Output rather than '
                'yielding it. The compute_fn of the core SolidDefinition must yield '
                'its results'
            ).format(solid_name=str(step.solid_handle))
        )

    if gen is None:
        return

    for result in gen:
        if isinstance(result, Output):
            compute_context.log.info(
                "Solid '{solid}' emitted output '{output}'".format(
                    solid=str(step.solid_handle), output=result.output_name
                )
            )
            yield Output(output_name=result.output_name, value=result.value)

        elif isinstance(result, Materialization):
            compute_context.log.info(
                "Solid '{solid}' materialized '{label}'".format(
                    solid=str(step.solid_handle), label=result.label
                )
            )

            yield result
        elif isinstance(result, ExpectationResult):
            compute_context.log.info(
                "Solid '{solid}' {status} expectation '{label}'".format(
                    solid=str(step.solid_handle),
                    status='passed' if result.success else 'failed',
                    label=result.label,
                )
            )

            yield result
        else:
            raise DagsterInvariantViolationError(
                (
                    'Compute function for solid {solid_name} yielded {result} rather than '
                    'an instance of the Output or Materialization class.'
                ).format(result=repr(result), solid_name=str(step.solid_handle))
            )


def _execute_core_compute(compute_context, inputs, compute_fn):
    '''
    Execute the user-specified compute for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(compute_context, 'compute_context', SystemComputeExecutionContext)
    check.dict_param(inputs, 'inputs', key_type=str)

    step = compute_context.step

    all_results = []
    for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
        yield step_output
        if isinstance(step_output, Output):
            all_results.append(step_output)

    if len(all_results) != len(step.step_outputs):
        emitted_result_names = {r.output_name for r in all_results}
        solid_output_names = {output.name for output in step.step_outputs}
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        compute_context.log.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=str(step.solid_handle), outputs=repr(omitted_outputs)
            )
        )
