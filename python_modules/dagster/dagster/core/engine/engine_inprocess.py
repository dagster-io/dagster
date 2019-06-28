import sys

from future.utils import raise_from

from dagster import check
from dagster.core.definitions import ExpectationResult, Materialization, Output
from dagster.core.errors import (
    DagsterError,
    DagsterExecutionStepExecutionError,
    DagsterInvariantViolationError,
    DagsterRuntimeCoercionError,
    DagsterStepOutputNotFoundError,
    DagsterTypeError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.config import ExecutorConfig
from dagster.core.execution.context.system import (
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)
from dagster.core.execution.plan.objects import (
    ExecutionStep,
    StepFailureData,
    StepOutputData,
    StepOutputHandle,
    StepSuccessData,
)
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.timing import time_execution_scope

from .engine_base import IEngine


class InProcessEngine(IEngine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan, step_keys_to_execute=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

        check.param_invariant(
            isinstance(pipeline_context.executor_config, ExecutorConfig),
            'pipeline_context',
            'Expected executor_config to be ExecutorConfig got {}'.format(
                pipeline_context.executor_config
            ),
        )

        failed_or_skipped_steps = set()

        step_levels = execution_plan.topological_step_levels()

        # It would be good to implement a reference tracking algorithm here so we could
        # garbage collection results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811
        for step_level in step_levels:
            for step in step_level:
                if step_key_set and step.key not in step_key_set:
                    continue

                step_context = pipeline_context.for_step(step)

                failed_inputs = [
                    step_input.prev_output_handle.step_key
                    for step_input in step.step_inputs
                    if step_input.is_from_output
                    and step_input.prev_output_handle.step_key in failed_or_skipped_steps
                ]
                if failed_inputs:
                    step_context.log.info(
                        (
                            'Dependencies for step {step} failed: {failed_inputs}. Not executing.'
                        ).format(step=step.key, failed_inputs=failed_inputs)
                    )
                    failed_or_skipped_steps.add(step.key)
                    yield DagsterEvent.step_skipped_event(step_context)
                    continue

                uncovered_inputs = pipeline_context.intermediates_manager.uncovered_inputs(
                    step_context, step
                )
                if uncovered_inputs:
                    # In partial pipeline execution, we may end up here without having validated the
                    # missing dependent outputs were optional
                    _assert_missing_inputs_optional(uncovered_inputs, execution_plan, step.key)

                    step_context.log.info(
                        (
                            'Not all inputs covered for {step}. Not executing. Output missing for '
                            'inputs: {uncovered_inputs}'
                        ).format(uncovered_inputs=uncovered_inputs, step=step.key)
                    )
                    failed_or_skipped_steps.add(step.key)
                    yield DagsterEvent.step_skipped_event(step_context)
                    continue

                for step_event in check.generator(dagster_event_sequence_for_step(step_context)):
                    check.inst(step_event, DagsterEvent)
                    if step_event.is_step_failure:
                        failed_or_skipped_steps.add(step.key)

                    yield step_event


def _assert_missing_inputs_optional(uncovered_inputs, execution_plan, step_key):
    nonoptionals = [
        handle for handle in uncovered_inputs if not execution_plan.get_step_output(handle).optional
    ]
    if nonoptionals:
        raise DagsterStepOutputNotFoundError(
            (
                'When executing {step} discovered required outputs missing '
                'from previous step: {nonoptionals}'
            ).format(nonoptionals=nonoptionals, step=step_key),
            step_key=nonoptionals[0].step_key,
            output_name=nonoptionals[0].output_name,
        )


def _create_input_values(step_context):
    step = step_context.step

    input_values = {}
    for step_input in step.step_inputs:
        if step_input.runtime_type.is_nothing:
            continue

        if step_input.is_from_output:
            input_value = step_context.intermediates_manager.get_intermediate(
                step_context, step_input.runtime_type, step_input.prev_output_handle
            )
        else:  # is from config
            input_value = step_input.runtime_type.input_schema.construct_from_config_value(
                step_context, step_input.config_data
            )
        input_values[step_input.name] = input_value

    return input_values


def dagster_event_sequence_for_step(step_context):
    '''
    Yield a sequence of dagster events for the given step with the step context.

    This function yields the events that directly result from the computation
    in the non-throwing case, and then also wraps that in an error boundary, so that
    any thrown exception gets translated in a step failure event, and then halts computation
    for that step.

    Additionally, if the pipeline is configured to reraise that error up through
    the execute_pipeline call (configured in the InProcessExecutorConfig) that
    reraise happens here.
    '''

    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    try:
        for step_event in check.generator(_core_dagster_event_sequence_for_step(step_context)):
            if step_event.event_type is DagsterEventType.STEP_OUTPUT:
                step_context.log.info(
                    'Step {step} emitted {value} for output {output}'.format(
                        step=step_context.step.key,
                        value=step_event.step_output_data.value_repr,
                        output=step_event.step_output_data.output_name,
                    )
                )
            yield step_event
    except DagsterError as dagster_error:
        user_facing_exc_info = (
            # pylint does not know original_exc_info exists is is_user_code_error is true
            # pylint: disable=no-member
            dagster_error.original_exc_info
            if dagster_error.is_user_code_error
            else sys.exc_info()
        )

        error_info = serializable_error_info_from_exc_info(user_facing_exc_info)

        yield DagsterEvent.step_failure_event(
            step_context=step_context, step_failure_data=StepFailureData(error=error_info)
        )

        if step_context.executor_config.raise_on_error:
            raise dagster_error

        return
    except Exception:  # pylint: disable=broad-except
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        yield DagsterEvent.step_failure_event(
            step_context=step_context, step_failure_data=StepFailureData(error=error_info)
        )
        raise


def _step_output_error_checked_event_sequence(step_context, event_sequence):
    '''
    Process the event sequence to check for invariant violations in the event
    sequence related to Output events emitted from the compute_fn.

    This consumes and emits an event sequence.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.generator_param(event_sequence, 'event_sequence')

    step = step_context.step
    output_names = list([output_def.name for output_def in step.step_outputs])
    seen_outputs = set()

    for event in event_sequence:
        if not isinstance(event, Output):
            yield event
            continue

        # do additional processing on Outputs
        result = event
        if not step.has_step_output(result.output_name):
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{result.output_name}" that does not exist. The available '
                'outputs are {output_names}'.format(
                    handle=str(step.solid_handle), result=result, output_names=output_names
                )
            )

        if result.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{result.output_name}" multiple times'.format(
                    handle=str(step.solid_handle), result=result
                )
            )

        yield result
        seen_outputs.add(result.output_name)

    for step_output_def in step.step_outputs:
        if not step_output_def.name in seen_outputs and not step_output_def.optional:
            if step_output_def.runtime_type.is_nothing:
                step_context.log.info(
                    'Emitting implicit Nothing for output "{output}" on solid {solid}'.format(
                        output=step_output_def.name, solid={str(step.solid_handle)}
                    )
                )
                yield Output(output_name=step_output_def.name, value=None)
            else:
                raise DagsterStepOutputNotFoundError(
                    'Core compute for solid "{handle}" did not return an output '
                    'for non-optional output "{step_output_def.name}"'.format(
                        handle=str(step.solid_handle), step_output_def=step_output_def
                    ),
                    step_key=step.key,
                    output_name=step_output_def.name,
                )


def _core_dagster_event_sequence_for_step(step_context):
    '''
    Execute the step within the step_context argument given the in-memory
    events. This function yields a sequence of DagsterEvents, but without
    catching any exceptions that have bubbled up during the computation
    of the step.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    inputs = _create_input_values(step_context)

    evaluated_inputs = {}
    # do runtime type checks of inputs versus step inputs
    for input_name, input_value in inputs.items():
        evaluated_inputs[input_name] = _get_evaluated_input(
            step_context.step, input_name, input_value
        )
    yield DagsterEvent.step_start_event(step_context)

    with time_execution_scope() as timer_result:
        event_sequence = check.generator(
            _event_sequence_for_step_compute_fn(step_context, evaluated_inputs)
        )

        # It is important for this loop to be indented within the
        # timer block above in order for time to be recorded accurately.
        for event in check.generator(
            _step_output_error_checked_event_sequence(step_context, event_sequence)
        ):

            if isinstance(event, Output):
                for evt in _create_step_output_events(step_context, event):
                    yield evt
            elif isinstance(event, Materialization):
                yield DagsterEvent.step_materialization(step_context, event)
            elif isinstance(event, ExpectationResult):
                yield DagsterEvent.step_expectation_result(step_context, event)
            else:
                check.failed(
                    'Unexpected event {event}, should have been caught earlier'.format(event=event)
                )

    yield DagsterEvent.step_success_event(
        step_context, StepSuccessData(duration_ms=timer_result.millis)
    )


def _create_step_output_events(step_context, result):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(result, 'result', Output)

    step = step_context.step
    step_output = step.step_output_named(result.output_name)

    try:
        value = step_output.runtime_type.coerce_runtime_value(result.value)

        step_output_handle = StepOutputHandle.from_step(step=step, output_name=result.output_name)

        object_key = step_context.intermediates_manager.set_intermediate(
            context=step_context,
            runtime_type=step_output.runtime_type,
            step_output_handle=step_output_handle,
            value=value,
        )

        yield DagsterEvent.step_output_event(
            step_context=step_context,
            step_output_data=StepOutputData(
                step_output_handle=step_output_handle,
                value_repr=repr(value),
                intermediate_materialization=Materialization.file(path=object_key)
                if object_key
                else None,
            ),
        )

        for evt in _create_output_materializations(step_context, result.output_name, value):
            yield evt

    except DagsterRuntimeCoercionError as e:
        raise DagsterInvariantViolationError(
            (
                'In solid "{handle}" the output "{output_name}" returned '
                'an invalid type: {error_msg}.'
            ).format(
                handle=str(step.solid_handle),
                error_msg=','.join(e.args),
                output_name=result.output_name,
            )
        )


def _create_output_materializations(step_context, output_name, value):
    step = step_context.step
    solid_config = step_context.environment_config.solids.get(str(step.solid_handle))
    if solid_config is None:
        return

    for output_spec in solid_config.outputs:
        check.invariant(len(output_spec) == 1)
        config_output_name, output_spec = list(output_spec.items())[0]
        if config_output_name == output_name:
            step_output = step.step_output_named(output_name)
            materialization = step_output.runtime_type.output_schema.materialize_runtime_value(
                step_context, output_spec, value
            )

            if not isinstance(materialization, Materialization):
                raise DagsterInvariantViolationError(
                    (
                        'materialize_runtime_value on type {type_name} has returned '
                        'value {value} of type {python_type}. You must return a '
                        'Materialization.'
                    ).format(
                        type_name=step_output.runtime_type.name,
                        value=repr(materialization),
                        python_type=type(materialization).__name__,
                    )
                )

            yield DagsterEvent.step_materialization(step_context, materialization)


def _get_evaluated_input(step, input_name, input_value):
    check.inst_param(step, 'step', ExecutionStep)
    check.str_param(input_name, 'input_name')

    step_input = step.step_input_named(input_name)
    try:
        return step_input.runtime_type.coerce_runtime_value(input_value)
    except DagsterRuntimeCoercionError as evaluate_error:
        raise_from(
            DagsterTypeError(
                (
                    'In solid "{handle}" the input "{input_name}" received value {input_value} '
                    'of Python type {input_type} which does not pass the typecheck for '
                    'Dagster type {step_input.runtime_type.name}. Step {step.key}.'
                ).format(
                    handle=str(step.solid_handle),
                    step=step,
                    input_name=input_name,
                    input_value=input_value,
                    input_type=type(input_value),
                    step_input=step_input,
                )
            ),
            evaluate_error,
        )


def _event_sequence_for_step_compute_fn(step_context, evaluated_inputs):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(evaluated_inputs, 'evaluated_inputs', key_type=str)

    error_str = '''Error occured during the execution of step:
    step key: "{key}"
    solid invocation: "{solid}"
    solid definition: "{solid_def}"
    '''.format(
        key=step_context.step.key,
        solid_def=step_context.solid_def.name,
        solid=step_context.solid.name,
    )

    with user_code_error_boundary(
        DagsterExecutionStepExecutionError,
        error_str,
        step_key=step_context.step.key,
        solid_def_name=step_context.solid_def.name,
        solid_name=step_context.solid.name,
    ):
        gen = check.opt_generator(step_context.step.compute_fn(step_context, evaluated_inputs))

        if gen is not None:
            for event in gen:
                yield event
