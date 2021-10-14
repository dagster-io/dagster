import time
from typing import Dict, List, Optional, cast

import pendulum
from dagster import check
from dagster.core.events import DagsterEvent, EngineEventData, log_step_event
from dagster.core.execution.context.system import PlanOrchestrationContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.execution.retries import RetryMode
from dagster.core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster.grpc.types import ExecuteStepArgs
from dagster.utils.backcompat import experimental

from ..base import Executor
from .step_handler import StepHandler


@experimental
class StepDelegatingExecutor(Executor):
    def __init__(
        self,
        step_handler: StepHandler,
        retries: RetryMode = RetryMode.DISABLED,
        sleep_seconds: Optional[float] = None,
        check_step_health_interval_seconds: Optional[int] = None,
    ):
        self._step_handler = step_handler
        self._retries = retries
        self._sleep_seconds = cast(
            float, check.opt_float_param(sleep_seconds, "sleep_seconds", default=0.1)
        )
        self._check_step_health_interval_seconds = cast(
            int,
            check.opt_int_param(
                check_step_health_interval_seconds, "check_step_health_interval_seconds", default=20
            ),
        )

    @property
    def retries(self):
        return self._retries

    def _pop_events(self, instance, run_id) -> List[DagsterEvent]:
        events = instance.logs_after(run_id, self._event_cursor)
        self._event_cursor += len(events)
        return [event.dagster_event for event in events if event.is_dagster_event]

    def _get_step_handler_context(
        self, pipeline_context, steps, active_execution
    ) -> StepHandlerContext:
        return StepHandlerContext(
            instance=pipeline_context.plan_data.instance,
            execute_step_args=ExecuteStepArgs(
                pipeline_origin=pipeline_context.reconstructable_pipeline.get_python_origin(),
                pipeline_run_id=pipeline_context.pipeline_run.run_id,
                step_keys_to_execute=[step.key for step in steps],
                instance_ref=pipeline_context.plan_data.instance.get_ref(),
                retry_mode=self.retries,
                known_state=active_execution.get_known_state(),
            ),
            step_tags={step.key: step.tags for step in steps},
            pipeline_run=pipeline_context.pipeline_run,
        )

    def _log_new_events(self, events, pipeline_context, running_steps):
        # Note: this could lead to duplicated events if the returned events were already logged
        # (they shouldn't be)
        for event in events:
            log_step_event(
                pipeline_context.for_step(running_steps[event.step_key]),
                event,
            )
        return events

    def execute(self, pipeline_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        check.inst_param(pipeline_context, "pipeline_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        self._event_cursor = -1  # pylint: disable=attribute-defined-outside-init

        yield DagsterEvent.engine_event(
            pipeline_context,
            f"Starting execution with step handler {self._step_handler.name}",
            EngineEventData(),
        )

        with execution_plan.start(retry_mode=self.retries) as active_execution:
            stopping = False
            running_steps: Dict[str, ExecutionStep] = {}

            last_check_step_health_time = pendulum.now("UTC")
            while (not active_execution.is_complete and not stopping) or running_steps:
                events = []

                if active_execution.check_for_interrupts():
                    yield DagsterEvent.engine_event(
                        pipeline_context,
                        "Executor received termination signal, forwarding to steps",
                        EngineEventData.interrupted(list(running_steps.keys())),
                    )
                    stopping = True
                    active_execution.mark_interrupted()
                    for _, step in running_steps.items():
                        events.extend(
                            self._log_new_events(
                                self._step_handler.terminate_step(
                                    self._get_step_handler_context(
                                        pipeline_context, [step], active_execution
                                    )
                                ),
                                pipeline_context,
                                running_steps,
                            )
                        )
                    running_steps.clear()

                events.extend(
                    self._pop_events(
                        pipeline_context.plan_data.instance,
                        pipeline_context.plan_data.pipeline_run.run_id,
                    )
                )

                if not stopping:
                    curr_time = pendulum.now("UTC")
                    if (
                        curr_time - last_check_step_health_time
                    ).total_seconds() >= self._check_step_health_interval_seconds:
                        last_check_step_health_time = curr_time
                        for _, step in running_steps.items():
                            events.extend(
                                self._log_new_events(
                                    self._step_handler.check_step_health(
                                        self._get_step_handler_context(
                                            pipeline_context, [step], active_execution
                                        )
                                    ),
                                    pipeline_context,
                                    running_steps,
                                )
                            )

                    for step in active_execution.get_steps_to_execute():
                        running_steps[step.key] = step
                        events.extend(
                            self._log_new_events(
                                self._step_handler.launch_step(
                                    self._get_step_handler_context(
                                        pipeline_context, [step], active_execution
                                    )
                                ),
                                pipeline_context,
                                running_steps,
                            )
                        )

                for dagster_event in events:
                    yield dagster_event
                    active_execution.handle_event(dagster_event)

                    if (
                        dagster_event.is_step_success
                        or dagster_event.is_step_failure
                        or dagster_event.is_step_skipped
                    ):
                        assert isinstance(dagster_event.step_key, str)
                        del running_steps[dagster_event.step_key]
                        active_execution.verify_complete(pipeline_context, dagster_event.step_key)

                # process skips from failures or uncovered inputs
                for event in active_execution.plan_events_iterator(pipeline_context):
                    yield event

                time.sleep(self._sleep_seconds)
