import sys
import time

import dagster._check as check
from celery.exceptions import TaskRevokedError
from dagster._core.errors import DagsterSubprocessError
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.storage.tags import PRIORITY_TAG
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster_shared.serdes import deserialize_value

from dagster_celery.defaults import task_default_priority, task_default_queue
from dagster_celery.make_app import make_app
from dagster_celery.tags import (
    DAGSTER_CELERY_QUEUE_TAG,
    DAGSTER_CELERY_RUN_PRIORITY_TAG,
    DAGSTER_CELERY_STEP_PRIORITY_TAG,
)

TICK_SECONDS = 1
DELEGATE_MARKER = "celery_queue_wait"


def core_celery_execution_loop(job_context, execution_plan, step_execution_fn):
    check.inst_param(job_context, "job_context", PlanOrchestrationContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.callable_param(step_execution_fn, "step_execution_fn")

    executor = job_context.executor

    # If there are no step keys to execute, then any io managers will not be used.
    if len(execution_plan.step_keys_to_execute) > 0:
        # https://github.com/dagster-io/dagster/issues/2440
        check.invariant(
            execution_plan.artifacts_persisted,
            "Cannot use in-memory storage with Celery, use filesystem (on top of NFS or "
            "similar system that allows files to be available to all nodes), S3, or GCS",
        )

    app = make_app(executor.app_args())

    priority_for_step = lambda step: (
        -1 * int(step.tags.get(DAGSTER_CELERY_STEP_PRIORITY_TAG, task_default_priority))
        + -1 * _get_run_priority(job_context)
    )
    priority_for_key = lambda step_key: (
        priority_for_step(execution_plan.get_step_by_key(step_key))
    )
    _warn_on_priority_misuse(job_context, execution_plan)

    step_results = {}  # Dict[ExecutionStep, celery.AsyncResult]
    step_errors = {}

    with execution_plan.start(
        retry_mode=job_context.executor.retries,
        sort_key_fn=priority_for_step,
    ) as active_execution:
        stopping = False

        while (not active_execution.is_complete and not stopping) or step_results:
            if active_execution.check_for_interrupts():
                yield DagsterEvent.engine_event(
                    job_context,
                    "Celery executor: received termination signal - revoking active tasks from"
                    " workers",
                    EngineEventData.interrupted(list(step_results.keys())),
                )
                stopping = True
                active_execution.mark_interrupted()
                for result in step_results.values():
                    result.revoke()
            results_to_pop = []
            for step_key, result in sorted(
                step_results.items(), key=lambda x: priority_for_key(x[0])
            ):
                if result.ready():
                    try:
                        step_events = result.get()
                    except TaskRevokedError:
                        step_events = []
                        step = active_execution.get_step_by_key(step_key)
                        yield DagsterEvent.engine_event(
                            job_context.for_step(step),
                            f'celery task for running step "{step_key}" was revoked.',
                            EngineEventData(marker_end=DELEGATE_MARKER),
                        )
                    except Exception:
                        # We will want to do more to handle the exception here.. maybe subclass Task
                        # Certainly yield an engine or job event
                        step_events = []
                        step_errors[step_key] = serializable_error_info_from_exc_info(
                            sys.exc_info()
                        )
                    for step_event in step_events:
                        event = deserialize_value(step_event, DagsterEvent)
                        yield event
                        active_execution.handle_event(event)

                    results_to_pop.append(step_key)

            for step_key in results_to_pop:
                if step_key in step_results:
                    del step_results[step_key]
                    active_execution.verify_complete(job_context, step_key)

            # process skips from failures or uncovered inputs
            for event in active_execution.plan_events_iterator(job_context):
                yield event

            # don't add any new steps if we are stopping
            if stopping or step_errors:
                continue

            # This is a slight refinement. If we have n workers idle and schedule m > n steps for
            # execution, the first n steps will be picked up by the idle workers in the order in
            # which they are scheduled (and the following m-n steps will be executed in priority
            # order, provided that it takes longer to execute a step than to schedule it). The test
            # case has m >> n to exhibit this behavior in the absence of this sort step.
            for step in active_execution.get_steps_to_execute():
                try:
                    queue = step.tags.get(DAGSTER_CELERY_QUEUE_TAG, task_default_queue)
                    yield DagsterEvent.engine_event(
                        job_context.for_step(step),
                        f'Submitting celery task for step "{step.key}" to queue "{queue}".',
                        EngineEventData(marker_start=DELEGATE_MARKER),
                    )

                    # Get the Celery priority for this step
                    priority = _get_step_priority(job_context, step)

                    # Submit the Celery tasks
                    step_results[step.key] = step_execution_fn(
                        app,
                        job_context,
                        step,
                        queue,
                        priority,
                        active_execution.get_known_state(),
                    )

                except Exception:
                    yield DagsterEvent.engine_event(
                        job_context,
                        "Encountered error during celery task submission.",
                        event_specific_data=EngineEventData.engine_error(
                            serializable_error_info_from_exc_info(sys.exc_info()),
                        ),
                    )
                    raise

            time.sleep(TICK_SECONDS)

        if step_errors:
            raise DagsterSubprocessError(
                "During celery execution errors occurred in workers:\n{error_list}".format(
                    error_list="\n".join(
                        [f"[{key}]: {err.to_string()}" for key, err in step_errors.items()]
                    )
                ),
                subprocess_error_infos=list(step_errors.values()),
            )


def _get_step_priority(context, step):
    """Step priority is (currently) set as the overall run priority plus the individual
    step priority.
    """
    run_priority = _get_run_priority(context)
    step_priority = int(step.tags.get(DAGSTER_CELERY_STEP_PRIORITY_TAG, task_default_priority))
    priority = run_priority + step_priority
    return priority


def _get_run_priority(context):
    if not context.has_tag(DAGSTER_CELERY_RUN_PRIORITY_TAG):
        return 0
    try:
        return int(context.get_tag(DAGSTER_CELERY_RUN_PRIORITY_TAG))
    except ValueError:
        return 0


def _warn_on_priority_misuse(context, execution_plan):
    bad_keys = []
    for key in execution_plan.step_keys_to_execute:
        step = execution_plan.get_step_by_key(key)
        if (
            step.tags.get(PRIORITY_TAG) is not None
            and step.tags.get(DAGSTER_CELERY_STEP_PRIORITY_TAG) is None
        ):
            bad_keys.append(key)

    if bad_keys:
        context.log.warn(
            'The following steps do not have "dagster-celery/priority" set but do '
            'have "dagster/priority" set which is not applicable for the celery engine: [{}]. '
            "Consider using a function to set both keys.".format(", ".join(bad_keys))
        )
