import os
import time
from typing import Dict, List, Optional, cast

import pendulum

import dagster._check as check
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    MetadataEntry,
    log_step_event,
)
from dagster.core.execution.context.system import PlanOrchestrationContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.execution.retries import RetryMode
from dagster.core.executor.step_delegating.step_handler.base import StepHandler, StepHandlerContext
from dagster.grpc.types import ExecuteStepArgs

from ..base import Executor

DEFAULT_SLEEP_SECONDS = float(
    os.environ.get("DAGSTER_STEP_DELEGATING_EXECUTOR_SLEEP_SECONDS", "1.0")
)


class StepDelegatingExecutor(Executor):
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
            execute_step_args=ExecuteStepArgs(
                pipeline_origin=plan_context.reconstructable_pipeline.get_python_origin(),
                pipeline_run_id=plan_context.pipeline_run.run_id,
                step_keys_to_execute=[step.key for step in steps],
                instance_ref=plan_context.plan_data.instance.get_ref(),
                retry_mode=self.retries.for_inner_plan(),
                known_state=active_execution.get_known_state(),
                should_verify_step=self._should_verify_step,
            ),
            step_tags={step.key: step.tags for step in steps},
            pipeline_run=plan_context.pipeline_run,
        )

    def _log_new_events(self, events, plan_context, running_steps):
        # Note: this could lead to duplicated events if the returned events were already logged
        # (they shouldn't be)
        for event in events:
            log_step_event(
                plan_context.for_step(running_steps[event.step_key]),
                event,
            )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        self._event_cursor = -1  # pylint: disable=attribute-defined-outside-init

        yield DagsterEvent.engine_event(
            plan_context,
            f"Starting execution with step handler {self._step_handler.name}",
            EngineEventData(),
        )

        with execution_plan.start(retry_mode=self.retries) as active_execution:
            running_steps: Dict[str, ExecutionStep] = {}

            if plan_context.resume_from_failure:
                yield DagsterEvent.engine_event(
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

                    yield DagsterEvent.engine_event(
                        plan_context,
                        "Checking on status of possibly launched steps",
                        EngineEventData(),
                        step.handle,
                    )

                    # TODO: check if failure event included. For now, hacky assumption that
                    # we don't log anything on successful check
                    if self._step_handler.check_step_health(
                        self._get_step_handler_context(plan_context, [step], active_execution)
                    ):
                        # health check failed, launch the step
                        self._log_new_events(
                            self._step_handler.launch_step(
                                self._get_step_handler_context(
                                    plan_context, [step], active_execution
                                )
                            ),
                            plan_context,
                            {step.key: step for step in possibly_in_flight_steps},
                        )

                    running_steps[step.key] = step

            last_check_step_health_time = pendulum.now("UTC")

            # Order of events is important here. During an interation, we call handle_event, then get_steps_to_execute,
            # then is_complete. get_steps_to_execute updates the state of ActiveExecution, and without it
            # is_complete can return true when we're just between steps.
            while not active_execution.is_complete:

                if active_execution.check_for_interrupts():
                    if not plan_context.instance.run_will_resume(plan_context.run_id):
                        yield DagsterEvent.engine_event(
                            plan_context,
                            "Executor received termination signal, forwarding to steps",
                            EngineEventData.interrupted(list(running_steps.keys())),
                        )
                        active_execution.mark_interrupted()
                        for _, step in running_steps.items():
                            self._log_new_events(
                                self._step_handler.terminate_step(
                                    self._get_step_handler_context(
                                        plan_context, [step], active_execution
                                    )
                                ),
                                plan_context,
                                running_steps,
                            )

                    else:
                        yield DagsterEvent.engine_event(
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
                        active_execution.mark_interrupted()

                    return

                for dagster_event in self._pop_events(
                    plan_context.instance,
                    plan_context.run_id,
                ):  # type: ignore

                    # STEP_SKIPPED events are only emitted by ActiveExecution, which already handles
                    # and yields them.
                    if dagster_event.is_step_skipped:
                        assert isinstance(dagster_event.step_key, str)
                        active_execution.verify_complete(plan_context, dagster_event.step_key)

                    else:
                        yield dagster_event
                        active_execution.handle_event(dagster_event)

                        if dagster_event.is_step_success or dagster_event.is_step_failure:
                            assert isinstance(dagster_event.step_key, str)
                            del running_steps[dagster_event.step_key]
                            active_execution.verify_complete(plan_context, dagster_event.step_key)

                # process skips from failures or uncovered inputs
                for event in active_execution.plan_events_iterator(plan_context):
                    yield event

                curr_time = pendulum.now("UTC")
                if (
                    curr_time - last_check_step_health_time
                ).total_seconds() >= self._check_step_health_interval_seconds:
                    last_check_step_health_time = curr_time
                    for _, step in running_steps.items():
                        self._log_new_events(
                            self._step_handler.check_step_health(
                                self._get_step_handler_context(
                                    plan_context, [step], active_execution
                                )
                            ),
                            plan_context,
                            running_steps,
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
                    self._log_new_events(
                        self._step_handler.launch_step(
                            self._get_step_handler_context(plan_context, [step], active_execution)
                        ),
                        plan_context,
                        running_steps,
                    )

                time.sleep(self._sleep_seconds)
