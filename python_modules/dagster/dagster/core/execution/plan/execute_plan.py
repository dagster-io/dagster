import sys
from typing import Iterator, List, Optional

from dagster import check
from dagster.core.definitions import Failure, HookExecutionResult, RetryRequested
from dagster.core.errors import (
    DagsterError,
    DagsterExecutionInterruptedError,
    DagsterUserCodeExecutionError,
    HookExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemExecutionContext, SystemStepExecutionContext
from dagster.core.execution.plan.execute_step import core_dagster_event_sequence_for_step
from dagster.core.execution.plan.objects import StepFailureData, StepRetryData, UserFailureData
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster.utils.types import ExcInfo


def inner_plan_execution_iterator(
    pipeline_context: SystemExecutionContext, execution_plan: ExecutionPlan
) -> Iterator[DagsterEvent]:
    check.inst_param(pipeline_context, "pipeline_context", SystemExecutionContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

    retries = pipeline_context.retries

    with execution_plan.start(retries=retries) as active_execution:

        # It would be good to implement a reference tracking algorithm here to
        # garbage collect results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811
        while not active_execution.is_complete:
            step = active_execution.get_next_step()
            step_context = pipeline_context.for_step(step)
            step_event_list = []

            missing_resources = [
                resource_key
                for resource_key in step_context.required_resource_keys
                if not hasattr(step_context.resources, resource_key)
            ]
            check.invariant(
                len(missing_resources) == 0,
                (
                    "Expected step context for solid {solid_name} to have all required resources, but "
                    "missing {missing_resources}."
                ).format(solid_name=step_context.solid.name, missing_resources=missing_resources),
            )

            # capture all of the logs for this step
            with pipeline_context.instance.compute_log_manager.watch(
                step_context.pipeline_run, step_context.step.key
            ):

                for step_event in check.generator(
                    _dagster_event_sequence_for_step(step_context, retries)
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


def _trigger_hook(
    step_context: SystemStepExecutionContext, step_event_list: List[DagsterEvent]
) -> Iterator[DagsterEvent]:
    """Trigger hooks and record hook's operatonal events"""
    hook_defs = step_context.pipeline_def.get_all_hooks_for_handle(step_context.solid_handle)
    # when the solid doesn't have a hook configured
    if hook_defs is None:
        return

    # when there are multiple hooks set on a solid, the hooks will run sequentially for the solid.
    # * we will not able to execute hooks asynchronously until we drop python 2.
    for hook_def in hook_defs:
        hook_context = step_context.for_hook(hook_def)

        try:
            with user_code_error_boundary(
                HookExecutionError,
                lambda: "Error occurred during the execution of hook_fn triggered for solid "
                '"{solid_name}"'.format(solid_name=step_context.solid.name),
            ):
                hook_execution_result = hook_def.hook_fn(hook_context, step_event_list)

        except HookExecutionError as hook_execution_error:
            # catch hook execution error and field a failure event instead of failing the pipeline run
            # is_hook_completed = False
            yield DagsterEvent.hook_errored(hook_context, hook_execution_error)
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
            yield DagsterEvent.hook_skipped(hook_context, hook_def)
        else:
            # hook_fn finishes successfully
            yield DagsterEvent.hook_completed(hook_context, hook_def)


def _dagster_event_sequence_for_step(
    step_context: SystemStepExecutionContext, retries: Retries
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

        (5) User error:
            The framework raised a DagsterError that indicates a usage error
            or some other error not communicated by a user-thrown exception. For example,
            if the user yields an object out of a compute function that is not a
            proper event (not an Output, ExpectationResult, etc).

        (6) Framework failure:
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
    """

    check.inst_param(step_context, "step_context", SystemStepExecutionContext)
    check.inst_param(retries, "retries", Retries)

    try:
        prior_attempt_count = retries.get_attempt_count(step_context.step.key)
        if step_context.step_launcher:
            step_events = step_context.step_launcher.launch_step(step_context, prior_attempt_count)
        else:
            step_events = core_dagster_event_sequence_for_step(step_context, prior_attempt_count)

        for step_event in check.generator(step_events):
            yield step_event

    # case (1) in top comment
    except RetryRequested as retry_request:
        retry_err_info = serializable_error_info_from_exc_info(sys.exc_info())

        if retries.disabled:
            fail_err = SerializableErrorInfo(
                message="RetryRequested but retries are disabled",
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
                    message="Exceeded max_retries of {}".format(retry_request.max_retries),
                    stack=retry_err_info.stack,
                    cls_name=retry_err_info.cls_name,
                    cause=retry_err_info.cause,
                )
                yield DagsterEvent.step_failure_event(
                    step_context=step_context,
                    step_failure_data=StepFailureData(error=fail_err, user_failure_data=None),
                )
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
        yield _step_failure_event_from_exc_info(
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
        yield _step_failure_event_from_exc_info(
            step_context,
            dagster_user_error.original_exc_info,
        )

        if step_context.raise_on_error:
            raise dagster_user_error.user_exception

    # case (4) in top comment
    except (KeyboardInterrupt, DagsterExecutionInterruptedError) as interrupt_error:
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())
        raise interrupt_error

    # case (5) in top comment
    except DagsterError as dagster_error:
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())

        if step_context.raise_on_error:
            raise dagster_error

    # case (6) in top comment
    except Exception as unexpected_exception:  # pylint: disable=broad-except
        yield _step_failure_event_from_exc_info(step_context, sys.exc_info())
        raise unexpected_exception


def _step_failure_event_from_exc_info(
    step_context: SystemStepExecutionContext,
    exc_info: ExcInfo,
    user_failure_data: Optional[UserFailureData] = None,
):
    return DagsterEvent.step_failure_event(
        step_context=step_context,
        step_failure_data=StepFailureData(
            error=serializable_error_info_from_exc_info(exc_info),
            user_failure_data=user_failure_data,
        ),
    )
