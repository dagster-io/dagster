import sys
from contextlib import ExitStack
from typing import Iterator, Sequence, cast

import dagster._check as check
from dagster._core.definitions import Failure, HookExecutionResult, RetryRequested
from dagster._core.errors import (
    DagsterError,
    DagsterExecutionInterruptedError,
    DagsterMaxRetriesExceededError,
    DagsterUserCodeExecutionError,
    HookExecutionError,
    user_code_error_boundary,
)
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.compute_logs import create_compute_log_file_key
from dagster._core.execution.context.system import PlanExecutionContext, StepExecutionContext
from dagster._core.execution.plan.execute_step import core_dagster_event_sequence_for_step
from dagster._core.execution.plan.objects import (
    ErrorSource,
    StepFailureData,
    StepRetryData,
    UserFailureData,
    step_failure_event_from_exc_info,
)
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


def inner_plan_execution_iterator(
    pipeline_context: PlanExecutionContext, execution_plan: ExecutionPlan
) -> Iterator[DagsterEvent]:
    check.inst_param(pipeline_context, "pipeline_context", PlanExecutionContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    compute_log_manager = pipeline_context.instance.compute_log_manager
    step_keys = [step.key for step in execution_plan.get_steps_to_execute_in_topo_order()]
    with execution_plan.start(retry_mode=pipeline_context.retry_mode) as active_execution:
        with ExitStack() as capture_stack:
            # begin capturing logs for the whole process if this is a captured log manager
            if isinstance(compute_log_manager, CapturedLogManager):
                file_key = create_compute_log_file_key()
                log_key = compute_log_manager.build_log_key_for_run(
                    pipeline_context.run_id, file_key
                )
                try:
                    log_context = capture_stack.enter_context(
                        compute_log_manager.capture_logs(log_key)
                    )
                    yield DagsterEvent.capture_logs(
                        pipeline_context, step_keys, log_key, log_context
                    )
                except Exception:
                    yield from _handle_compute_log_setup_error(pipeline_context, sys.exc_info())

            # It would be good to implement a reference tracking algorithm here to
            # garbage collect results that are no longer needed by any steps
            # https://github.com/dagster-io/dagster/issues/811
            while not active_execution.is_complete:
                step = active_execution.get_next_step()
                step_context = cast(
                    StepExecutionContext,
                    pipeline_context.for_step(step, active_execution.get_known_state()),
                )
                step_event_list = []

                missing_resources = [
                    resource_key
                    for resource_key in step_context.required_resource_keys
                    if not hasattr(step_context.resources, resource_key)
                ]
                check.invariant(
                    len(missing_resources) == 0,
                    (
                        "Expected step context for solid {solid_name} to have all required"
                        " resources, but missing {missing_resources}."
                    ).format(
                        solid_name=step_context.solid.name, missing_resources=missing_resources
                    ),
                )

                with ExitStack() as step_stack:
                    if not isinstance(compute_log_manager, CapturedLogManager):
                        # capture all of the logs for individual steps
                        try:
                            step_stack.enter_context(
                                pipeline_context.instance.compute_log_manager.watch(
                                    step_context.pipeline_run, step_context.step.key
                                )
                            )
                            yield DagsterEvent.legacy_compute_log_step_event(step_context)
                        except Exception:
                            yield from _handle_compute_log_setup_error(step_context, sys.exc_info())

                        for step_event in check.generator(
                            dagster_event_sequence_for_step(step_context)
                        ):
                            check.inst(step_event, DagsterEvent)
                            step_event_list.append(step_event)
                            yield step_event
                            active_execution.handle_event(step_event)

                        active_execution.verify_complete(pipeline_context, step.key)

                        try:
                            step_stack.close()
                        except Exception:
                            yield from _handle_compute_log_teardown_error(
                                step_context, sys.exc_info()
                            )
                    else:
                        # we have already set up the log capture at the process level, just handle the
                        # step events
                        for step_event in check.generator(
                            dagster_event_sequence_for_step(step_context)
                        ):
                            check.inst(step_event, DagsterEvent)
                            step_event_list.append(step_event)
                            yield step_event
                            active_execution.handle_event(step_event)

                        active_execution.verify_complete(pipeline_context, step.key)

                # process skips from failures or uncovered inputs
                for event in active_execution.plan_events_iterator(pipeline_context):
                    step_event_list.append(event)
                    yield event

                # pass a list of step events to hooks
                for hook_event in _trigger_hook(step_context, step_event_list):
                    yield hook_event

            try:
                capture_stack.close()
            except Exception:
                yield from _handle_compute_log_teardown_error(pipeline_context, sys.exc_info())


def _handle_compute_log_setup_error(context, exc_info):
    yield DagsterEvent.engine_event(
        plan_context=context,
        message="Exception while setting up compute log capture",
        event_specific_data=EngineEventData(error=serializable_error_info_from_exc_info(exc_info)),
    )


def _handle_compute_log_teardown_error(context, exc_info):
    yield DagsterEvent.engine_event(
        plan_context=context,
        message="Exception while cleaning up compute log capture",
        event_specific_data=EngineEventData(error=serializable_error_info_from_exc_info(exc_info)),
    )


def _trigger_hook(
    step_context: StepExecutionContext, step_event_list: Sequence[DagsterEvent]
) -> Iterator[DagsterEvent]:
    """Trigger hooks and record hook's operatonal events."""
    hook_defs = step_context.pipeline_def.get_all_hooks_for_handle(step_context.solid_handle)
    # when the solid doesn't have a hook configured
    if hook_defs is None:
        return

    op_label = step_context.describe_op()

    # when there are multiple hooks set on a solid, the hooks will run sequentially for the solid.
    # * we will not able to execute hooks asynchronously until we drop python 2.
    for hook_def in hook_defs:
        hook_context = step_context.for_hook(hook_def)

        try:
            with user_code_error_boundary(
                HookExecutionError,
                lambda: f"Error occurred during the execution of hook_fn triggered for {op_label}",
                log_manager=hook_context.log,
            ):
                hook_execution_result = hook_def.hook_fn(hook_context, step_event_list)

        except HookExecutionError as hook_execution_error:
            # catch hook execution error and field a failure event instead of failing the pipeline run
            yield DagsterEvent.hook_errored(step_context, hook_execution_error)
            continue

        check.invariant(
            isinstance(hook_execution_result, HookExecutionResult),
            (
                "Error in hook {hook_name}: hook unexpectedly returned result {result} of "
                "type {type_}. Should be a HookExecutionResult"
            ).format(
                hook_name=hook_def.name,
                result=hook_execution_result,
                type_=type(hook_execution_result),
            ),
        )
        if hook_execution_result and hook_execution_result.is_skipped:
            # when the triggering condition didn't meet in the hook_fn, for instance,
            # a @success_hook decorated user-defined function won't run on a failed solid
            # but internally the hook_fn still runs, so we yield HOOK_SKIPPED event instead
            yield DagsterEvent.hook_skipped(step_context, hook_def)
        else:
            # hook_fn finishes successfully
            yield DagsterEvent.hook_completed(step_context, hook_def)


def dagster_event_sequence_for_step(
    step_context: StepExecutionContext, force_local_execution: bool = False
) -> Iterator[DagsterEvent]:
    """
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

        (4) Execution interrupted:
            The run was interrupted in the middle of execution (typically by a
            termination request).

        (5) Dagster framework error:
            The framework raised a DagsterError that indicates a usage error
            or some other error not communicated by a user-thrown exception. For example,
            if the user yields an object out of a compute function that is not a
            proper event (not an Output, ExpectationResult, etc).

        (6) All other errors:
            An unexpected error occurred. Either there has been an internal error in the framework
            OR we have forgotten to put a user code error boundary around invoked user-space code.


    The "raised_dagster_errors" context manager can be used to force these errors to be
    re-raised and surfaced to the user. This is mostly to get sensible errors in test and
    ad-hoc contexts, rather than forcing the user to wade through the
    PipelineExecutionResult API in order to find the step that failed.

    For tools, however, this option should be false, and a sensible error message
    signaled to the user within that tool.

    When we launch a step that has a step launcher, we use this function on both the host process
    and the remote process. When we run the step in the remote process, to prevent an infinite loop
    of launching steps that then launch steps, and so on, the remote process will run this with
    the force_local_execution argument set to True.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)

    try:
        if step_context.step_launcher and not force_local_execution:
            # info all on step_context - should deprecate second arg
            step_events = step_context.step_launcher.launch_step(step_context)
        else:
            step_events = core_dagster_event_sequence_for_step(step_context)

        for step_event in check.generator(step_events):
            yield step_event

    # case (1) in top comment
    except RetryRequested as retry_request:
        retry_err_info = serializable_error_info_from_exc_info(sys.exc_info())

        if step_context.retry_mode.disabled:
            fail_err = SerializableErrorInfo(
                message="RetryRequested but retries are disabled",
                stack=retry_err_info.stack,
                cls_name=retry_err_info.cls_name,
                cause=retry_err_info.cause,
            )
            step_context.capture_step_exception(retry_request)
            yield DagsterEvent.step_failure_event(
                step_context=step_context,
                step_failure_data=StepFailureData(error=fail_err, user_failure_data=None),
            )
        else:  # retries.enabled or retries.deferred
            prev_attempts = step_context.previous_attempt_count
            if prev_attempts >= retry_request.max_retries:
                fail_err = SerializableErrorInfo(
                    message=f"Exceeded max_retries of {retry_request.max_retries}\n",
                    stack=retry_err_info.stack,
                    cls_name=retry_err_info.cls_name,
                    cause=retry_err_info.cause,
                )
                step_context.capture_step_exception(retry_request)
                yield DagsterEvent.step_failure_event(
                    step_context=step_context,
                    step_failure_data=StepFailureData(
                        error=fail_err,
                        user_failure_data=None,
                        # set the flag to omit the outer stack if we have a cause to show
                        error_source=ErrorSource.USER_CODE_ERROR if fail_err.cause else None,
                    ),
                )
                if step_context.raise_on_error:
                    raise DagsterMaxRetriesExceededError.from_error_info(fail_err)
            else:
                yield DagsterEvent.step_retry_event(
                    step_context,
                    StepRetryData(
                        error=retry_err_info,
                        seconds_to_wait=retry_request.seconds_to_wait,
                    ),
                )

    # case (2) in top comment
    except Failure as failure:
        step_context.capture_step_exception(failure)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            UserFailureData(
                label="intentional-failure",
                description=failure.description,
                metadata_entries=failure.metadata_entries,
            ),
        )
        if step_context.raise_on_error:
            raise failure

    # case (3) in top comment
    except DagsterUserCodeExecutionError as dagster_user_error:
        step_context.capture_step_exception(dagster_user_error.user_exception)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            error_source=ErrorSource.USER_CODE_ERROR,
        )

        if step_context.raise_on_error:
            raise dagster_user_error.user_exception

    # case (4) in top comment
    except (KeyboardInterrupt, DagsterExecutionInterruptedError) as interrupt_error:
        step_context.capture_step_exception(interrupt_error)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            error_source=ErrorSource.INTERRUPT,
        )
        raise interrupt_error

    # cases (5) and (6) in top comment
    except BaseException as error:
        step_context.capture_step_exception(error)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            error_source=ErrorSource.FRAMEWORK_ERROR
            if isinstance(error, DagsterError)
            else ErrorSource.UNEXPECTED_ERROR,
        )

        if step_context.raise_on_error:
            raise error
