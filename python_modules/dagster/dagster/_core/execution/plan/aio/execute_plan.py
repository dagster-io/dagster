import inspect
import sys
from collections.abc import AsyncIterator, Sequence

from dagster_shared import check
from dagster_shared.error import DagsterError, SerializableErrorInfo

from dagster._core.definitions import Failure, HookExecutionResult, RetryRequested
from dagster._core.errors import (
    DagsterExecutionInterruptedError,
    DagsterMaxRetriesExceededError,
    DagsterUserCodeExecutionError,
    HookExecutionError,
    user_code_error_boundary,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.aio.execute_step import core_dagster_event_sequence_for_step
from dagster._core.execution.plan.execute_plan import _user_failure_data_for_exc
from dagster._core.execution.plan.objects import (
    ErrorSource,
    StepFailureData,
    StepRetryData,
    step_failure_event_from_exc_info,
)
from dagster._utils.error import serializable_error_info_from_exc_info


async def dagster_event_sequence_for_step(
    step_context: StepExecutionContext, force_local_execution: bool = False
) -> AsyncIterator[DagsterEvent]:
    """Yield a sequence of dagster events for the given step with the step context.

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
    JobExecutionResult API in order to find the step that failed.

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
            raise NotImplementedError("Step launchers not implemented in async context")
        else:
            step_events = core_dagster_event_sequence_for_step(step_context)

        async for step_event in step_events:
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
                step_failure_data=StepFailureData(
                    error=fail_err,
                    user_failure_data=_user_failure_data_for_exc(retry_request.__cause__),
                ),
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
                        user_failure_data=_user_failure_data_for_exc(retry_request.__cause__),
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
            _user_failure_data_for_exc(failure),
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
            error_source=(
                ErrorSource.FRAMEWORK_ERROR
                if isinstance(error, DagsterError)
                else ErrorSource.UNEXPECTED_ERROR
            ),
        )

        if step_context.raise_on_error:
            raise error


async def _trigger_hook(
    step_context: StepExecutionContext, step_event_list: Sequence[DagsterEvent]
) -> AsyncIterator[DagsterEvent]:
    """Trigger hooks and record hook's operatonal events."""
    hook_defs = step_context.job_def.get_all_hooks_for_handle(step_context.node_handle)
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
                if inspect.iscoroutinefunction(hook_def.hook_fn):
                    hook_execution_result = await hook_def.hook_fn(hook_context, step_event_list)
                else:
                    hook_execution_result = hook_def.hook_fn(hook_context, step_event_list)

        except HookExecutionError as hook_execution_error:
            # catch hook execution error and field a failure event instead of failing the pipeline run
            yield DagsterEvent.hook_errored(step_context, hook_execution_error)
            continue

        check.invariant(
            isinstance(hook_execution_result, HookExecutionResult),
            (
                f"Error in hook {hook_def.name}: hook unexpectedly returned result {hook_execution_result} of "
                f"type {type(hook_execution_result)}. Should be a HookExecutionResult"
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
