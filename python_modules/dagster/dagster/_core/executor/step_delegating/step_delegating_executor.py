import os
import sys
import time
from typing import Dict, List, Optional, cast

import pendulum

import dagster._check as check
from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData, MetadataEntry
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.plan.objects import StepFailureData
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.step_delegating.step_handler.base import StepHandler, StepHandlerContext
from dagster._grpc.types import ExecuteStepArgs
from dagster._utils.error import serializable_error_info_from_exc_info

from ..base import Executor

DEFAULT_SLEEP_SECONDS = float(
    os.environ.get("DAGSTER_STEP_DELEGATING_EXECUTOR_SLEEP_SECONDS", "1.0")
)


class StepDelegatingExecutor(Executor):
    """This executor tails the event log for events from the steps that it spins up. It also
    sometimes creates its own events - when it does, that event is automatically written to the
    event log. But we wait until we later tail it from the event log database before yielding it,
    to avoid yielding the same event multiple times to callsites."""

    def __init__(
        self,
        step_handler: StepHandler,
        retries: RetryMode,
        sleep_seconds: Optional[float] = None,
        check_step_health_interval_seconds: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        should_verify_step: bool = False,
    ):
        self._step_handler = step_handler
        self._retries = retries

        self._max_concurrent = check.opt_int_param(max_concurrent, "max_concurrent")
        if self._max_concurrent is not None:
            check.invariant(self._max_concurrent > 0, "max_concurrent must be > 0")

        self._sleep_seconds = cast(
            float,
            check.opt_float_param(sleep_seconds, "sleep_seconds", default=DEFAULT_SLEEP_SECONDS),
        )
        self._check_step_health_interval_seconds = cast(
            int,
            check.opt_int_param(
                check_step_health_interval_seconds, "check_step_health_interval_seconds", default=20
            ),
        )
        self._should_verify_step = should_verify_step

    @property
    def retries(self):
        return self._retries

    def _pop_events(self, instance, run_id) -> List[DagsterEvent]:
        events = instance.logs_after(run_id, self._event_cursor, of_type=set(DagsterEventType))
        self._event_cursor += len(events)
        dagster_events = [event.dagster_event for event in events]
        check.invariant(None not in dagster_events, "Query should not return a non dagster event")
        return dagster_events

    def _get_step_handler_context(
        self, plan_context, steps, active_execution
    ) -> StepHandlerContext:
        return StepHandlerContext(
            instance=plan_context.plan_data.instance,
            plan_context=plan_context,
            steps=steps,
            execute_step_args=ExecuteStepArgs(
                pipeline_origin=plan_context.reconstructable_pipeline.get_python_origin(),
                pipeline_run_id=plan_context.pipeline_run.run_id,
                step_keys_to_execute=[step.key for step in steps],
                instance_ref=plan_context.plan_data.instance.get_ref(),
                retry_mode=self.retries.for_inner_plan(),
                known_state=active_execution.get_known_state(),
                should_verify_step=self._should_verify_step,
            ),
            pipeline_run=plan_context.pipeline_run,
        )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        self._event_cursor = -1  # pylint: disable=attribute-defined-outside-init

        DagsterEvent.engine_event(
            plan_context,
            f"Starting execution with step handler {self._step_handler.name}.",
            EngineEventData(),
        )

        with execution_plan.start(retry_mode=self.retries) as active_execution:
            running_steps: Dict[str, ExecutionStep] = {}

            if plan_context.resume_from_failure:
                DagsterEvent.engine_event(
                    plan_context,
                    "Resuming execution from failure",
                    EngineEventData(),
                )

                prior_events = self._pop_events(
                    plan_context.instance,
                    plan_context.run_id,
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
                        health_check = self._step_handler.check_step_health(step_handler_context)
                    except Exception:
                        # For now we assume that an exception indicates that the step should be resumed.
                        # This should probably be a separate should_resume_step method on the step handler.
                        DagsterEvent.engine_event(
                            step_handler_context.get_step_context(step.key),
                            f"Including {step.key} in the new run since it raised an error when checking whether it was running",
                            EngineEventData(
                                error=serializable_error_info_from_exc_info(sys.exc_info())
                            ),
                        )
                        should_retry_step = True
                    else:
                        if not health_check.is_healthy:
                            DagsterEvent.engine_event(
                                step_handler_context.get_step_context(step.key),
                                f"Including step {step.key} in the new run since it is not currently running: {health_check.unhealthy_reason}",
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

            last_check_step_health_time = pendulum.now("UTC")

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
                        for _, step in running_steps.items():
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
                            "Executor received termination signal, not forwarding to steps because "
                            "run will be resumed",
                            EngineEventData(
                                metadata_entries=[
                                    MetadataEntry(
                                        "steps_in_flight", value=str(running_steps.keys())
                                    )
                                ]
                            ),
                        )

                    return

                for dagster_event in self._pop_events(
                    plan_context.instance,
                    plan_context.run_id,
                ):  # type: ignore

                    yield dagster_event
                    # STEP_SKIPPED events are only emitted by ActiveExecution, which already handles
                    # and yields them.

                    if dagster_event.is_step_skipped:
                        assert isinstance(dagster_event.step_key, str)
                        active_execution.verify_complete(plan_context, dagster_event.step_key)
                    else:
                        active_execution.handle_event(dagster_event)
                        if (
                            dagster_event.is_step_success
                            or dagster_event.is_step_failure
                            or dagster_event.is_resource_init_failure
                        ):
                            assert isinstance(dagster_event.step_key, str)
                            del running_steps[dagster_event.step_key]
                            active_execution.verify_complete(plan_context, dagster_event.step_key)

                # process skips from failures or uncovered inputs
                list(active_execution.plan_events_iterator(plan_context))

                curr_time = pendulum.now("UTC")
                if (
                    curr_time - last_check_step_health_time
                ).total_seconds() >= self._check_step_health_interval_seconds:
                    last_check_step_health_time = curr_time
                    for _, step in running_steps.items():

                        step_context = plan_context.for_step(step)

                        try:
                            health_check_result = self._step_handler.check_step_health(
                                self._get_step_handler_context(
                                    plan_context, [step], active_execution
                                )
                            )
                            if not health_check_result.is_healthy:
                                DagsterEvent.step_failure_event(
                                    step_context=step_context,
                                    step_failure_data=StepFailureData(
                                        error=None,
                                        user_failure_data=None,
                                    ),
                                    message=f"Step {step.key} failed health check: {health_check_result.unhealthy_reason}",
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

                for step in active_execution.get_steps_to_execute(max_steps_to_run):
                    running_steps[step.key] = step
                    list(
                        self._step_handler.launch_step(
                            self._get_step_handler_context(plan_context, [step], active_execution)
                        )
                    )

                time.sleep(self._sleep_seconds)
