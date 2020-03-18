import sys

from dagster import check
from dagster.core.definitions import (
    ExpectationResult,
    Failure,
    Materialization,
    Output,
    RetryRequested,
    TypeCheck,
)
from dagster.core.errors import (
    DagsterError,
    DagsterExecutionStepExecutionError,
    DagsterInputHydrationConfigError,
    DagsterInvariantViolationError,
    DagsterOutputMaterializationError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckDidNotPass,
    DagsterTypeCheckError,
    DagsterUserCodeExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.compute_logs import mirror_step_io
from dagster.core.execution.context.system import (
    SystemPipelineExecutionContext,
    SystemStepExecutionContext,
)
from dagster.core.execution.memoization import copy_required_intermediates_for_execution
from dagster.core.execution.plan.objects import (
    StepFailureData,
    StepInputData,
    StepOutputData,
    StepOutputHandle,
    StepRetryData,
    StepSuccessData,
    TypeCheckData,
    UserFailureData,
)
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries
from dagster.core.storage.object_store import ObjectStoreOperation
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster.utils.timing import time_execution_scope


def inner_plan_execution_iterator(pipeline_context, execution_plan, retries):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(retries, 'retries', Retries)

    for event in copy_required_intermediates_for_execution(pipeline_context, execution_plan):
        yield event

    # It would be good to implement a reference tracking algorithm here to
    # garbage collect results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811
    active_execution = execution_plan.start(retries=retries)
    while not active_execution.is_complete:
        step = active_execution.get_next_step()

        step_context = pipeline_context.for_step(step)
        check.invariant(
            all(
                hasattr(step_context.resources, resource_key)
                for resource_key in step_context.required_resource_keys
            ),
            'expected step context to have all required resources',
        )

        with mirror_step_io(step_context):
            # capture all of the logs for this step
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
                yield DagsterEvent.step_skipped_event(step_context)
                active_execution.mark_skipped(step.key)
            else:
                for step_event in check.generator(
                    dagster_event_sequence_for_step(step_context, retries)
                ):
                    check.inst(step_event, DagsterEvent)
                    yield step_event
                    active_execution.handle_event(step_event)

            active_execution.verify_complete(pipeline_context, step.key)

        # process skips from failures or uncovered inputs
        for event in active_execution.skipped_step_events_iterator(pipeline_context):
            yield event


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


class MultipleStepOutputsListWrapper(list):
    pass


def _input_values_from_intermediates_manager(step_context):
    step = step_context.step

    input_values = {}
    for step_input in step.step_inputs:
        if step_input.dagster_type.kind == DagsterTypeKind.NOTHING:
            continue

        if step_input.is_from_multiple_outputs:
            if hasattr(step_input.dagster_type, 'inner_type'):
                dagster_type = step_input.dagster_type.inner_type
            else:  # This is the case where the fan-in is typed Any
                dagster_type = step_input.dagster_type
            _input_value = [
                step_context.intermediates_manager.get_intermediate(
                    context=step_context,
                    step_output_handle=source_handle,
                    dagster_type=dagster_type,
                )
                for source_handle in step_input.source_handles
            ]
            # When we're using an object store-backed intermediate store, we wrap the
            # ObjectStoreOperation[] representing the fan-in values in a MultipleStepOutputsListWrapper
            # so we can yield the relevant object store events and unpack the values in the caller
            if all((isinstance(x, ObjectStoreOperation) for x in _input_value)):
                input_value = MultipleStepOutputsListWrapper(_input_value)
            else:
                input_value = _input_value

        elif step_input.is_from_single_output:
            input_value = step_context.intermediates_manager.get_intermediate(
                context=step_context,
                step_output_handle=step_input.source_handles[0],
                dagster_type=step_input.dagster_type,
            )

        else:  # is from config

            def _generate_error_boundary_msg_for_step_input(_context, _input):
                return lambda: '''Error occurred during input hydration:
                input name: "{input}"
                step key: "{key}"
                solid invocation: "{solid}"
                solid definition: "{solid_def}"
                '''.format(
                    input=_input.name,
                    key=_context.step.key,
                    solid_def=_context.solid_def.name,
                    solid=_context.solid.name,
                )

            with user_code_error_boundary(
                DagsterInputHydrationConfigError,
                msg_fn=_generate_error_boundary_msg_for_step_input(step_context, step_input),
            ):
                input_value = step_input.dagster_type.input_hydration_config.construct_from_config_value(
                    step_context, step_input.config_data
                )
        input_values[step_input.name] = input_value

    return input_values


def dagster_event_sequence_for_step(step_context, retries):
    '''
    Yield a sequence of dagster events for the given step with the step context.

    This function also processes errors. It handles a few error cases:

        (1) User code requests to be retried:
            A RetryRequested has been raised. We will either put the step in to
            up_for_retry state or a failure state depending on the number of previous attempts
            and the max_retries on the received RetryRequested.

        (2) User code fails successfully:
            The user-space code has raised a Failure which may have
            explicit metadata attached.

        (3) User code fails unexpectedly:
            The user-space code has raised an Exception. It has been
            wrapped in an exception derived from DagsterUserCodeException. In that
            case the original user exc_info is stashed on the exception
            as the original_exc_info property.

        (4) User error:
            The framework raised a DagsterError that indicates a usage error
            or some other error not communicated by a user-thrown exception. For example,
            if the user yields an object out of a compute function that is not a
            proper event (not an Output, ExpectationResult, etc).

        (5) Framework failure or interrupt:
            An unexpected error occurred. This is a framework error. Either there
            has been an internal error in the framework OR we have forgotten to put a
            user code error boundary around invoked user-space code. These terminate
            the computation immediately (by re-raising).


    The "raised_dagster_errors" context manager can be used to force these errors to be
    re-raised and surfaced to the user. This is mostly to get sensible errors in test and
    ad-hoc contexts, rather than forcing the user to wade through the
    PipelineExecutionResult API in order to find the step that failed.

    For tools, however, this option should be false, and a sensible error message
    signaled to the user within that tool.
    '''

    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)

    try:
        for step_event in check.generator(
            _core_dagster_event_sequence_for_step(step_context, retries)
        ):
            yield step_event

    # case (1) in top comment
    except RetryRequested as retry_request:
        retry_err_info = serializable_error_info_from_exc_info(sys.exc_info())

        if retries.disabled:
            fail_err = SerializableErrorInfo(
                message='RetryRequested but retries are disabled',
                stack=retry_err_info.stack,
                cls_name=retry_err_info.cls_name,
                cause=retry_err_info.cause,
            )
            yield DagsterEvent.step_failure_event(
                step_context=step_context,
                step_failure_data=StepFailureData(error=fail_err, user_failure_data=None),
            )
        else:  # retries.enabled or retries.deferred
            prev_attempts = retries.get_attempt_count(step_context.step.key)
            if prev_attempts >= retry_request.max_retries:
                fail_err = SerializableErrorInfo(
                    message='Exceeded max_retries of {}'.format(retry_request.max_retries),
                    stack=retry_err_info.stack,
                    cls_name=retry_err_info.cls_name,
                    cause=retry_err_info.cause,
                )
                yield DagsterEvent.step_failure_event(
                    step_context=step_context,
                    step_failure_data=StepFailureData(error=fail_err, user_failure_data=None),
                )
            else:
                attempt_num = prev_attempts + 1
                yield DagsterEvent.step_retry_event(
                    step_context,
                    StepRetryData(
                        error=retry_err_info, seconds_to_wait=retry_request.seconds_to_wait,
                    ),
                )

    # case (2) in top comment
    except Failure as failure:
        yield _step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            UserFailureData(
                label='intentional-failure',
                description=failure.description,
                metadata_entries=failure.metadata_entries,
            ),
        )
        if step_context.raise_on_error:
            raise failure

    # case (3) in top comment
    except DagsterUserCodeExecutionError as dagster_user_error:
        yield _step_failure_event_from_exc_info(
            step_context, dagster_user_error.original_exc_info,
        )

        if step_context.raise_on_error:
            raise dagster_user_error.user_exception

    # case (4) in top comment
    except DagsterError as dagster_error:
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        if step_context.raise_on_error:
            raise dagster_error

    # case (5) in top comment
    except (Exception, KeyboardInterrupt) as unexpected_exception:  # pylint: disable=broad-except
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        raise unexpected_exception


def _step_failure_event_from_exc_info(step_context, exc_info, user_failure_data=None):
    return DagsterEvent.step_failure_event(
        step_context=step_context,
        step_failure_data=StepFailureData(
            error=serializable_error_info_from_exc_info(exc_info),
            user_failure_data=user_failure_data,
        ),
    )


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
            if step_output_def.dagster_type.kind == DagsterTypeKind.NOTHING:
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


def _do_type_check(context, dagster_type, value):
    type_check = dagster_type.type_check(context, value)
    if not isinstance(type_check, TypeCheck):
        return TypeCheck(
            success=False,
            description=(
                'Type checks must return TypeCheck. Type check for type {type_name} returned '
                'value of type {return_type} when checking runtime value of type {dagster_type}.'
            ).format(
                type_name=dagster_type.name, return_type=type(type_check), dagster_type=type(value)
            ),
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


def _type_checked_event_sequence_for_input(step_context, input_name, input_value):
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    check.str_param(input_name, 'input_name')

    step_input = step_context.step.step_input_named(input_name)
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
            dagster_type_name=step_input.dagster_type.name,
            step_key=step_context.step.key,
        ),
    ):
        type_check = _do_type_check(
            step_context.for_type(step_input.dagster_type), step_input.dagster_type, input_value,
        )

        yield _create_step_input_event(
            step_context, input_name, type_check=type_check, success=type_check.success
        )

        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description='Type check failed for step input {input_name} of type {dagster_type}.'.format(
                    input_name=input_name, dagster_type=step_input.dagster_type.name,
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=step_input.dagster_type,
            )


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
            dagster_type_name=step_output.dagster_type.name,
            step_key=step_context.step.key,
        ),
    ):
        type_check = _do_type_check(
            step_context.for_type(step_output.dagster_type), step_output.dagster_type, output.value
        )

        yield _create_step_output_event(
            step_context, output, type_check=type_check, success=type_check.success
        )

        if not type_check.success:
            raise DagsterTypeCheckDidNotPass(
                description='Type check failed for step output {output_name} of type {dagster_type}.'.format(
                    output_name=output.output_name, dagster_type=step_output.dagster_type.name,
                ),
                metadata_entries=type_check.metadata_entries,
                dagster_type=step_output.dagster_type,
            )


def _core_dagster_event_sequence_for_step(step_context, retries):
    '''
    Execute the step within the step_context argument given the in-memory
    events. This function yields a sequence of DagsterEvents, but without
    catching any exceptions that have bubbled up during the computation
    of the step.
    '''
    check.inst_param(step_context, 'step_context', SystemStepExecutionContext)
    attempts = retries.get_attempt_count(step_context.step.key)
    if attempts > 0:
        yield DagsterEvent.step_restarted_event(step_context, attempts)
    else:
        yield DagsterEvent.step_start_event(step_context)

    inputs = {}
    for input_name, input_value in _input_values_from_intermediates_manager(step_context).items():
        if isinstance(input_value, ObjectStoreOperation):
            yield DagsterEvent.object_store_operation(
                step_context, ObjectStoreOperation.serializable(input_value, value_name=input_name)
            )
            inputs[input_name] = input_value.obj
        elif isinstance(input_value, MultipleStepOutputsListWrapper):
            for op in input_value:
                yield DagsterEvent.object_store_operation(
                    step_context, ObjectStoreOperation.serializable(op, value_name=input_name)
                )
            inputs[input_name] = [op.obj for op in input_value]
        else:
            inputs[input_name] = input_value

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

    for evt in _set_intermediates(step_context, step_output, step_output_handle, output):
        yield evt

    for evt in _create_output_materializations(step_context, output.output_name, output.value):
        yield evt


def _set_intermediates(step_context, step_output, step_output_handle, output):
    res = step_context.intermediates_manager.set_intermediate(
        context=step_context,
        dagster_type=step_output.dagster_type,
        step_output_handle=step_output_handle,
        value=output.value,
    )
    if isinstance(res, ObjectStoreOperation):
        yield DagsterEvent.object_store_operation(
            step_context, ObjectStoreOperation.serializable(res, value_name=output.output_name)
        )


def _create_output_materializations(step_context, output_name, value):
    step = step_context.step
    current_handle = step.solid_handle

    # check for output mappings at every point up the composition hierarchy
    while current_handle:
        solid_config = step_context.environment_config.solids.get(current_handle.to_string())
        current_handle = current_handle.parent

        if solid_config is None:
            continue

        for output_spec in solid_config.outputs:
            check.invariant(len(output_spec) == 1)
            config_output_name, output_spec = list(output_spec.items())[0]
            if config_output_name == output_name:
                step_output = step.step_output_named(output_name)
                with user_code_error_boundary(
                    DagsterOutputMaterializationError,
                    msg_fn=lambda: '''Error occurred during output materialization:
                    output name: "{output_name}"
                    step key: "{key}"
                    solid invocation: "{solid}"
                    solid definition: "{solid_def}"
                    '''.format(
                        output_name=output_name,
                        key=step_context.step.key,
                        solid_def=step_context.solid_def.name,
                        solid=step_context.solid.name,
                    ),
                ):
                    materializations = step_output.dagster_type.output_materialization_config.materialize_runtime_values(
                        step_context, output_spec, value
                    )

                for materialization in materializations:
                    if not isinstance(materialization, Materialization):
                        raise DagsterInvariantViolationError(
                            (
                                'materialize_runtime_values on type {type_name} has returned '
                                'value {value} of type {python_type}. You must return a '
                                'Materialization.'
                            ).format(
                                type_name=step_output.dagster_type.name,
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
        control_flow_exceptions=[Failure, RetryRequested],
        msg_fn=lambda: '''Error occurred during the execution of step:
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
