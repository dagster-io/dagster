import logging
import math
import os
import sys
import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional, cast

import dagster._check as check
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.event_api import EventLogCursor
from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.plan.active import ActiveExecution
from dagster._core.execution.plan.instance_concurrency_context import InstanceConcurrencyContext
from dagster._core.execution.plan.objects import StepFailureData
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.execution.step_dependency_config import StepDependencyConfig
from dagster._core.executor.base import Executor
from dagster._core.executor.step_delegating.step_handler.base import StepHandler, StepHandlerContext
from dagster._core.instance import DagsterInstance
from dagster._grpc.types import ExecuteStepArgs
from dagster._time import get_current_datetime
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._core.execution.plan.step import ExecutionStep


def _default_sleep_seconds():
    return float(os.environ.get("DAGSTER_STEP_DELEGATING_EXECUTOR_SLEEP_SECONDS", "1.0"))


class StepDelegatingExecutor(Executor):
    """This executor tails the event log for events from the steps that it spins up. It also
    sometimes creates its own events - when it does, that event is automatically written to the
    event log. But we wait until we later tail it from the event log database before yielding it,
    to avoid yielding the same event multiple times to callsites.
    """

    def __init__(
        self,
        step_handler: StepHandler,
        retries: RetryMode,
        sleep_seconds: Optional[float] = None,
        check_step_health_interval_seconds: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[list[dict[str, Any]]] = None,
        should_verify_step: bool = False,
        step_dependency_config: StepDependencyConfig = StepDependencyConfig.default(),
    ):
        self._step_handler = step_handler
        self._retries = retries
        self._step_dependency_config = step_dependency_config

        self._max_concurrent = check.opt_int_param(max_concurrent, "max_concurrent")
        self._tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits, "tag_concurrency_limits"
        )

        if self._max_concurrent is not None:
            check.invariant(self._max_concurrent > 0, "max_concurrent must be > 0")

        self._sleep_seconds = cast(
            "float",
            check.opt_float_param(sleep_seconds, "sleep_seconds", default=_default_sleep_seconds()),
        )
        self._check_step_health_interval_seconds = cast(
            "int",
            check.opt_int_param(
                check_step_health_interval_seconds, "check_step_health_interval_seconds", default=20
            ),
        )
        self._should_verify_step = should_verify_step

        self._event_cursor: Optional[str] = None

        self._pop_events_limit = int(os.getenv("DAGSTER_EXECUTOR_POP_EVENTS_LIMIT", "1000"))

    @property
    def retries(self):
        return self._retries

    @property
    def step_dependency_config(self) -> StepDependencyConfig:
        return self._step_dependency_config

    def _get_pop_events_offset(self, instance: DagsterInstance):
        if "DAGSTER_EXECUTOR_POP_EVENTS_OFFSET" in os.environ:
            return int(os.environ["DAGSTER_EXECUTOR_POP_EVENTS_OFFSET"])
        return instance.event_log_storage.default_run_scoped_event_tailer_offset()

    def _pop_events(
        self, instance: DagsterInstance, run_id: str, seen_storage_ids: set[int]
    ) -> Sequence[DagsterEvent]:
        conn = instance.get_records_for_run(
            run_id,
            self._event_cursor,
            of_type=set(DagsterEventType),
            limit=self._pop_events_limit,
        )

        dagster_events = [
            record.event_log_entry.dagster_event
            for record in conn.records
            if record.event_log_entry.dagster_event and record.storage_id not in seen_storage_ids
        ]

        returned_storage_ids = {record.storage_id for record in conn.records}

        pop_events_offset = self._get_pop_events_offset(instance)

        if not pop_events_offset:
            self._event_cursor = conn.cursor
        elif (
            len(returned_storage_ids) == self._pop_events_limit
            and returned_storage_ids <= seen_storage_ids
        ):
            # Start the next cursor halfway through the returned list
            desired_next_storage_id = conn.records[
                math.ceil(self._pop_events_limit / 2) - 1
            ].storage_id
            self._event_cursor = EventLogCursor.from_storage_id(desired_next_storage_id).to_string()

            logging.getLogger("dagster").warn(
                f"Event tailer query returned a list of {self._pop_events_limit} storage IDs that had already been returned before. Setting the cursor to {desired_next_storage_id} to ensure it advances."
            )
        else:
            cursor_obj = EventLogCursor.parse(conn.cursor)
            check.invariant(
                cursor_obj.is_id_cursor(),
                "Applying a tailer offset only works with an id-based cursor",
            )
            # Apply offset for next query (while also making sure that the cursor doesn't backtrack)
            current_cursor_storage_id = (
                EventLogCursor.parse(self._event_cursor).storage_id() if self._event_cursor else 0
            )
            new_storage_id = max(
                current_cursor_storage_id, cursor_obj.storage_id() - pop_events_offset
            )
            self._event_cursor = EventLogCursor.from_storage_id(new_storage_id).to_string()

        seen_storage_ids.update(returned_storage_ids)

        return dagster_events

    def _get_step_handler_context(
        self, plan_context, steps, active_execution
    ) -> StepHandlerContext:
        return StepHandlerContext(
            instance=plan_context.plan_data.instance,
            plan_context=plan_context,
            steps=steps,
            execute_step_args=ExecuteStepArgs(
                job_origin=plan_context.reconstructable_job.get_python_origin(),
                run_id=plan_context.dagster_run.run_id,
                step_keys_to_execute=[step.key for step in steps],
                instance_ref=plan_context.plan_data.instance.get_ref(),
                retry_mode=self.retries.for_inner_plan(),
                known_state=active_execution.get_known_state(),
                should_verify_step=self._should_verify_step,
                print_serialized_events=False,
            ),
            dagster_run=plan_context.dagster_run,
        )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        seen_storage_ids = set()

        DagsterEvent.engine_event(
            plan_context,
            f"Starting execution with step handler {self._step_handler.name}.",
            EngineEventData(),
        )
        with InstanceConcurrencyContext(
            plan_context.instance, plan_context.dagster_run
        ) as instance_concurrency_context:
            with ActiveExecution(
                execution_plan,
                retry_mode=self.retries,
                max_concurrent=self._max_concurrent,
                tag_concurrency_limits=self._tag_concurrency_limits,
                instance_concurrency_context=instance_concurrency_context,
                step_dependency_config=self.step_dependency_config,
            ) as active_execution:
                running_steps: dict[str, ExecutionStep] = {}

                if plan_context.resume_from_failure:
                    DagsterEvent.engine_event(
                        plan_context,
                        "Resuming execution from failure",
                        EngineEventData(),
                    )

                    prior_events = self._pop_events(
                        plan_context.instance,
                        plan_context.run_id,
                        seen_storage_ids,
                    )
                    for dagster_event in prior_events:
                        yield dagster_event

                    possibly_in_flight_steps = active_execution.rebuild_from_events(prior_events)
                    for step in possibly_in_flight_steps:
                        step_handler_context = self._get_step_handler_context(
                            plan_context, [step], active_execution
                        )

                        DagsterEvent.engine_event(
                            step_handler_context.get_step_context(step.key),
                            f"Checking on status of in-progress step {step.key} from previous run",
                            EngineEventData(),
                        )

                        should_retry_step = False
                        health_check = None

                        try:
                            health_check = self._step_handler.check_step_health(
                                step_handler_context
                            )
                        except Exception:
                            # For now we assume that an exception indicates that the step should be resumed.
                            # This should probably be a separate should_resume_step method on the step handler.
                            DagsterEvent.engine_event(
                                step_handler_context.get_step_context(step.key),
                                f"Including {step.key} in the new run since it raised an error"
                                " when checking whether it was running",
                                EngineEventData(
                                    error=serializable_error_info_from_exc_info(sys.exc_info())
                                ),
                            )
                            should_retry_step = True
                        else:
                            if not health_check.is_healthy:
                                DagsterEvent.engine_event(
                                    step_handler_context.get_step_context(step.key),
                                    f"Including step {step.key} in the new run since it is not"
                                    f" currently running: {health_check.unhealthy_reason}",
                                    EngineEventData(),
                                )
                                should_retry_step = True

                        if should_retry_step:
                            # health check failed, launch the step
                            list(
                                self._step_handler.launch_step(
                                    self._get_step_handler_context(
                                        plan_context, [step], active_execution
                                    )
                                )
                            )

                        running_steps[step.key] = step

                last_check_step_health_time = get_current_datetime()

                try:
                    # Order of events is important here. During an interation, we call handle_event, then get_steps_to_execute,
                    # then is_complete. get_steps_to_execute updates the state of ActiveExecution, and without it
                    # is_complete can return true when we're just between steps.
                    while not active_execution.is_complete:
                        if active_execution.check_for_interrupts():
                            active_execution.mark_interrupted()
                            if not plan_context.instance.run_will_resume(plan_context.run_id):
                                DagsterEvent.engine_event(
                                    plan_context,
                                    "Executor received termination signal, forwarding to steps",
                                    EngineEventData.interrupted(list(running_steps.keys())),
                                )
                                for step in running_steps.values():
                                    list(
                                        self._step_handler.terminate_step(
                                            self._get_step_handler_context(
                                                plan_context, [step], active_execution
                                            )
                                        )
                                    )
                            else:
                                DagsterEvent.engine_event(
                                    plan_context,
                                    "Executor received termination signal, not forwarding to steps"
                                    " because run will be resumed",
                                    EngineEventData(
                                        metadata={
                                            "steps_in_flight": MetadataValue.text(
                                                str(running_steps.keys())
                                            )
                                        },
                                    ),
                                )

                            return

                        if active_execution.has_in_flight_steps:
                            for dagster_event in self._pop_events(
                                plan_context.instance,
                                plan_context.run_id,
                                seen_storage_ids,
                            ):
                                yield dagster_event
                                # STEP_SKIPPED events are only emitted by ActiveExecution, which already handles
                                # and yields them.

                                if dagster_event.is_step_skipped:
                                    assert isinstance(dagster_event.step_key, str)
                                    active_execution.verify_complete(
                                        plan_context, dagster_event.step_key
                                    )
                                else:
                                    active_execution.handle_event(dagster_event)
                                    if (
                                        dagster_event.is_step_success
                                        or dagster_event.is_step_failure
                                        or dagster_event.is_resource_init_failure
                                        or dagster_event.is_step_up_for_retry
                                    ):
                                        assert isinstance(dagster_event.step_key, str)
                                        del running_steps[dagster_event.step_key]

                                        if not dagster_event.is_step_up_for_retry:
                                            active_execution.verify_complete(
                                                plan_context, dagster_event.step_key
                                            )

                        # process skips from failures or uncovered inputs
                        list(active_execution.plan_events_iterator(plan_context))

                        curr_time = get_current_datetime()
                        if (
                            curr_time - last_check_step_health_time
                        ).total_seconds() >= self._check_step_health_interval_seconds:
                            last_check_step_health_time = curr_time
                            for step in running_steps.values():
                                step_context = plan_context.for_step(step)

                                try:
                                    health_check_result = self._step_handler.check_step_health(
                                        self._get_step_handler_context(
                                            plan_context, [step], active_execution
                                        )
                                    )
                                    if not health_check_result.is_healthy:
                                        health_check_error = SerializableErrorInfo(
                                            message=f"Step {step.key} failed health check: {health_check_result.unhealthy_reason}",
                                            stack=[],
                                            cls_name=None,
                                        )

                                        self.get_failure_or_retry_event_after_crash(
                                            step_context,
                                            health_check_error,
                                            active_execution.get_known_state(),
                                        )

                                except Exception:
                                    serializable_error = serializable_error_info_from_exc_info(
                                        sys.exc_info()
                                    )
                                    # Log a step failure event if there was an error during the health
                                    # check
                                    DagsterEvent.step_failure_event(
                                        step_context=plan_context.for_step(step),
                                        step_failure_data=StepFailureData(
                                            error=serializable_error,
                                            user_failure_data=None,
                                        ),
                                    )

                        if self._max_concurrent is not None:
                            max_steps_to_run = self._max_concurrent - len(running_steps)
                            check.invariant(
                                max_steps_to_run >= 0, "More steps are active than max_concurrent"
                            )
                        else:
                            max_steps_to_run = None  # disables limit

                        # process events from concurrency blocked steps
                        list(active_execution.concurrency_event_iterator(plan_context))

                        for step in active_execution.get_steps_to_execute(max_steps_to_run):
                            running_steps[step.key] = step
                            list(
                                self._step_handler.launch_step(
                                    self._get_step_handler_context(
                                        plan_context, [step], active_execution
                                    )
                                )
                            )

                        time.sleep(self._sleep_seconds)
                except Exception:
                    if not active_execution.is_complete and running_steps:
                        serializable_error = serializable_error_info_from_exc_info(sys.exc_info())
                        DagsterEvent.engine_event(
                            plan_context,
                            "Unexpected exception while steps were still in-progress - terminating running steps:",
                            EngineEventData(
                                metadata={
                                    "steps_interrupted": MetadataValue.text(
                                        str(list(running_steps.keys()))
                                    )
                                },
                                error=serializable_error,
                            ),
                        )
                        for step in running_steps.values():
                            list(
                                self._step_handler.terminate_step(
                                    self._get_step_handler_context(
                                        plan_context, [step], active_execution
                                    )
                                )
                            )
                    raise
