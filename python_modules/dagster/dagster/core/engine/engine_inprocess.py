import sys

from dagster import check
from dagster.core.definitions import ExpectationResult, Materialization, Output, Failure, TypeCheck
from dagster.core.errors import (
    DagsterError,
    DagsterExecutionStepExecutionError,
    DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.config import ExecutorConfig
from dagster.core.execution.context.system import (
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)
from dagster.core.execution.plan.objects import (
    StepFailureData,
    StepInputData,
    StepOutputData,
    StepOutputHandle,
    StepSuccessData,
    TypeCheckData,
    UserFailureData,
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


def _input_values_from_intermediates_manager(step_context):
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
            input_value = step_input.runtime_type.input_hydration_config.construct_from_config_value(
                step_context, step_input.config_data
            )
        input_values[step_input.name] = input_value

    return input_values


def _step_failure_event_from_exc_info(step_context, exc_info, user_failure_data=None):
    return DagsterEvent.step_failure_event(
        step_context=step_context,
        step_failure_data=StepFailureData(
            error=serializable_error_info_from_exc_info(exc_info),
            user_failure_data=user_failure_data,
        ),
    )


def dagster_event_sequence_for_step(step_context):
    '''
    Yield a sequence of dagster events for the given step with the step context.

    Thie function also processes errors. It handles a few error cases:
        (1) The user-space code has raised an Exception. It has been
        wrapped in an exception derived from DagsterUserCodeException. In that
        case the original user exc_info is stashed on the exception
        as the original_exc_info property. Examples of this are computations
        with the compute_fn, and type checks. If the user has raised an
        intentional error via throwing Failure, they can also optionally
        pass along explicit metadata attached to that Failure.
        (2) The framework raised a DagsterError that indicates a usage error
        or some other error not communicated by a user-thrown exception. For example,
        if the user yields an object out of a compute function that is not a
        proper event (not an Output, ExpectationResult, etc).
        (3) An unexpected error occured. This is a framework error. Either there
        has been an internal error in the framewore OR we have forgtten to put a
        user code error boundary around invoked user-space code. These terminate
        the computation immediately (by re-raising) even if raise_on_error is false.

    If the raise_on_error option is set to True, these errors are reraised and surfaced
    to the user. This is mostly to get sensible errors in test and ad-hoc contexts, rather
    than forcing the user to wade through the PipelineExecutionResult API in order to find
    the step that errored.

    For tools, however, this option should be false, and a sensible error message
    signaled to the user within that tool.
    '''

    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    try:
        for step_event in check.generator(_core_dagster_event_sequence_for_step(step_context)):
            yield step_event

    # case (1) in top comment
    except DagsterUserCodeExecutionError as dagster_user_error:  # case (1) above
        yield _step_failure_event_from_exc_info(
            step_context,
            dagster_user_error.original_exc_info,
            UserFailureData(
                label='intentional-failure',
                description=dagster_user_error.user_specified_failure.description,
                metadata_entries=dagster_user_error.user_specified_failure.metadata_entries,
            )
            if dagster_user_error.is_user_specified_failure
            else None,
        )

        if step_context.executor_config.raise_on_error:
            raise dagster_user_error

    # case (2) in top comment
    except DagsterError as dagster_error:
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        if step_context.executor_config.raise_on_error:
            raise dagster_error

    # case (3) in top comment
    except Exception as unexpected_exception:  # pylint: disable=broad-except
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        raise unexpected_exception


def _step_output_error_checked_user_event_sequence(step_context, user_event_sequence):
    '''
    Process the event sequence to check for invariant violations in the event
    sequence related to Output events emitted from the compute_fn.

    This consumes and emits an event sequence.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.generator_param(user_event_sequence, 'user_event_sequence')

    step = step_context.step
    output_names = list([output_def.name for output_def in step.step_outputs])
    seen_outputs = set()

    for user_event in user_event_sequence:
        if not isinstance(user_event, Output):
            yield user_event
            continue

        # do additional processing on Outputs
        output = user_event
        if not step.has_step_output(output.output_name):
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{output.output_name}" that does not exist. The available '
                'outputs are {output_names}'.format(
                    handle=str(step.solid_handle), output=output, output_names=output_names
                )
            )

        if output.output_name in seen_outputs:
            raise DagsterInvariantViolationError(
                'Core compute for solid "{handle}" returned an output '
                '"{output.output_name}" multiple times'.format(
                    handle=str(step.solid_handle), output=output
                )
            )

        yield output
        seen_outputs.add(output.output_name)

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


def _do_type_check(runtime_type, value):
    type_check = runtime_type.type_check(value)
    if type_check is not None and not isinstance(type_check, TypeCheck):
        raise DagsterInvariantViolationError(
            (
                'Type checks can only return None or TypeCheck. Type '
                '{type_name} returned {value}.'
            ).format(type_name=runtime_type.name, value=repr(type_check))
        )
    return type_check


def _create_step_input_event(step_context, input_name, type_check, success):
    return DagsterEvent.step_input_event(
        step_context,
        StepInputData(
            input_name=input_name,
            type_check_data=TypeCheckData(
                success=success,
                label=input_name,
                description=type_check.description if type_check else None,
                metadata_entries=type_check.metadata_entries if type_check else [],
            ),
        ),
    )


def _type_check_from_failure(failure):
    check.inst_param(failure, 'failure', Exception)

    # TypeScript this ain't. pylint not aware of type discrimination
    # pylint: disable=no-member

    return (
        TypeCheck(failure.user_exception.description, failure.user_exception.metadata_entries)
        if isinstance(failure, DagsterTypeCheckError)
        and isinstance(failure.user_exception, Failure)
        else TypeCheck(str(failure), metadata_entries=[])
    )


def _type_checked_event_sequence_for_input(step_context, input_name, input_value):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.str_param(input_name, 'input_name')

    step_input = step_context.step.step_input_named(input_name)
    try:
        with user_code_error_boundary(
            DagsterTypeCheckError,
            lambda: (
                'In solid "{handle}" the input "{input_name}" received '
                'value {input_value} of Python type {input_type} which '
                'does not pass the typecheck for Dagster type '
                '{dagster_type_name}. Step {step_key}.'
            ).format(
                handle=str(step_context.step.solid_handle),
                input_name=input_name,
                input_value=input_value,
                input_type=type(input_value),
                dagster_type_name=step_input.runtime_type.name,
                step_key=step_context.step.key,
            ),
        ):
            yield _create_step_input_event(
                step_context,
                input_name,
                type_check=_do_type_check(step_input.runtime_type, input_value),
                success=True,
            )
    except Exception as failure:  # pylint: disable=broad-except
        yield _create_step_input_event(
            step_context, input_name, type_check=_type_check_from_failure(failure), success=False
        )

        raise failure


def _create_step_output_event(step_context, output, type_check, success):
    return DagsterEvent.step_output_event(
        step_context=step_context,
        step_output_data=StepOutputData(
            step_output_handle=StepOutputHandle.from_step(
                step=step_context.step, output_name=output.output_name
            ),
            type_check_data=TypeCheckData(
                success=success,
                label=output.output_name,
                description=type_check.description if type_check else None,
                metadata_entries=type_check.metadata_entries if type_check else [],
            ),
        ),
    )


def _type_checked_step_output_event_sequence(step_context, output):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(output, 'output', Output)

    step_output = step_context.step.step_output_named(output.output_name)
    try:
        with user_code_error_boundary(
            DagsterTypeCheckError,
            lambda: (
                'In solid "{handle}" the output "{output_name}" received '
                'value {output_value} of Python type {output_type} which '
                'does not pass the typecheck for Dagster type '
                '{dagster_type_name}. Step {step_key}.'
            ).format(
                handle=str(step_context.step.solid_handle),
                output_name=output.output_name,
                output_value=output.value,
                output_type=type(output.value),
                dagster_type_name=step_output.runtime_type.name,
                step_key=step_context.step.key,
            ),
        ):
            yield _create_step_output_event(
                step_context,
                output,
                type_check=_do_type_check(step_output.runtime_type, output.value),
                success=True,
            )
    except Exception as failure:  # pylint: disable=broad-except
        yield _create_step_output_event(
            step_context, output, type_check=_type_check_from_failure(failure), success=False
        )

        raise failure


def _core_dagster_event_sequence_for_step(step_context):
    '''
    Execute the step within the step_context argument given the in-memory
    events. This function yields a sequence of DagsterEvents, but without
    catching any exceptions that have bubbled up during the computation
    of the step.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    yield DagsterEvent.step_start_event(step_context)

    inputs = _input_values_from_intermediates_manager(step_context)

    for input_name, input_value in inputs.items():
        for evt in check.generator(
            _type_checked_event_sequence_for_input(step_context, input_name, input_value)
        ):
            yield evt

    with time_execution_scope() as timer_result:
        user_event_sequence = check.generator(
            _user_event_sequence_for_step_compute_fn(step_context, inputs)
        )

        # It is important for this loop to be indented within the
        # timer block above in order for time to be recorded accurately.
        for user_event in check.generator(
            _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
        ):

            if isinstance(user_event, Output):
                for evt in _create_step_events_for_output(step_context, user_event):
                    yield evt
            elif isinstance(user_event, Materialization):
                yield DagsterEvent.step_materialization(step_context, user_event)
            elif isinstance(user_event, ExpectationResult):
                yield DagsterEvent.step_expectation_result(step_context, user_event)
            else:
                check.failed(
                    'Unexpected event {event}, should have been caught earlier'.format(
                        event=user_event
                    )
                )

    yield DagsterEvent.step_success_event(
        step_context, StepSuccessData(duration_ms=timer_result.millis)
    )


def _create_step_events_for_output(step_context, output):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.inst_param(output, 'output', Output)

    step = step_context.step
    step_output = step.step_output_named(output.output_name)

    for output_event in _type_checked_step_output_event_sequence(step_context, output):
        yield output_event

    step_output_handle = StepOutputHandle.from_step(step=step, output_name=output.output_name)

    step_context.intermediates_manager.set_intermediate(
        context=step_context,
        runtime_type=step_output.runtime_type,
        step_output_handle=step_output_handle,
        value=output.value,
    )

    for evt in _create_output_materializations(step_context, output.output_name, output.value):
        yield evt


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
            materialization = step_output.runtime_type.output_materialization_config.materialize_runtime_value(
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


def _user_event_sequence_for_step_compute_fn(step_context, evaluated_inputs):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.dict_param(evaluated_inputs, 'evaluated_inputs', key_type=str)

    with user_code_error_boundary(
        DagsterExecutionStepExecutionError,
        msg_fn=lambda: '''Error occured during the execution of step:
        step key: "{key}"
        solid invocation: "{solid}"
        solid definition: "{solid_def}"
        '''.format(
            key=step_context.step.key,
            solid_def=step_context.solid_def.name,
            solid=step_context.solid.name,
        ),
        step_key=step_context.step.key,
        solid_def_name=step_context.solid_def.name,
        solid_name=step_context.solid.name,
    ):
        gen = check.opt_generator(step_context.step.compute_fn(step_context, evaluated_inputs))

        if gen is not None:
            for event in gen:
                yield event
