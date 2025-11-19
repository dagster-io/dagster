import os
import queue
import sys
from collections.abc import AsyncIterator, Iterator
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any, Optional, ParamSpec, TypeVar

import anyio
import anyio.abc
from anyio.from_thread import start_blocking_portal
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from dagster_shared.utils.timing import format_duration

import dagster._check as check
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.api import ExecuteRunWithPlanIterable
from dagster._core.execution.compute_logs import create_compute_log_file_key
from dagster._core.execution.context.system import PlanExecutionContext, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import PlanExecutionContextManager
from dagster._core.execution.plan.active import ActiveExecution
from dagster._core.execution.plan.aio.execute_plan import (
    _trigger_hook,
    dagster_event_sequence_for_step,
)
from dagster._core.execution.plan.aio.execute_step import _verify_if_complete
from dagster._core.execution.plan.execute_plan import _handle_compute_log_setup_error
from dagster._core.execution.plan.instance_concurrency_context import InstanceConcurrencyContext
from dagster._core.execution.plan.objects import step_failure_event_from_exc_info
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.execution.retries import RetryMode
from dagster._core.execution.step_dependency_config import StepDependencyConfig
from dagster._core.executor.base import Executor
from dagster._utils.timing import time_execution_scope

T = TypeVar("T")
P = ParamSpec("P")

_SENTINEL = object()
_SYNC_ASYNC_BRIDGE_QUEUE_MAXSIZE = 0


@dataclass
class _ErrorWrapper:
    exc: BaseException


class AsyncExecutor(Executor):
    def __init__(
        self,
        retries: RetryMode,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[list[dict[str, Any]]] = None,
        step_dependency_config: StepDependencyConfig = StepDependencyConfig.default(),
    ):
        self._retries = check.inst_param(retries, "retries", RetryMode)
        self._step_dependency_config = check.inst_param(
            step_dependency_config, "step_dependency_config", StepDependencyConfig
        )
        self._max_concurrent = check.opt_int_param(max_concurrent, "max_concurrent")
        self._tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits, "tag_concurrency_limits"
        )

    @property
    def retries(self) -> RetryMode:
        return self._retries

    @property
    def step_dependency_config(self) -> StepDependencyConfig:
        return self._step_dependency_config

    def execute(
        self,
        plan_context: PlanOrchestrationContext,
        execution_plan: ExecutionPlan,
    ) -> Iterator[DagsterEvent]:
        """Synchronous entrypoint.

        Uses ExecuteRunWithPlanIterable to get a PlanExecutionContext, but the
        actual scheduling logic is defined by this executor via
        _async_execution_iterator.
        """
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        step_keys_to_execute = execution_plan.step_keys_to_execute

        yield DagsterEvent.engine_event(
            plan_context,
            "Executing steps with AsyncExecutor",
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

        with time_execution_scope() as timer_result:
            yield from ExecuteRunWithPlanIterable(
                execution_plan=execution_plan,
                iterator=self._execution_iterator_wrapper,
                execution_context_manager=PlanExecutionContextManager(
                    job=plan_context.job,
                    retry_mode=plan_context.retry_mode,
                    execution_plan=execution_plan,
                    run_config=plan_context.run_config,
                    dagster_run=plan_context.dagster_run,
                    instance=plan_context.instance,
                    raise_on_error=plan_context.raise_on_error,
                    output_capture=plan_context.output_capture,
                    step_dependency_config=self.step_dependency_config,
                ),
            )

        yield DagsterEvent.engine_event(
            plan_context,
            f"Finished AsyncExecutor in {format_duration(timer_result.millis)}",
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

    def _execution_iterator_wrapper(
        self,
        job_context: PlanExecutionContext,
        execution_plan: ExecutionPlan,
    ) -> Iterator[DagsterEvent]:
        """Synchronous wrapper around the async execution iterator.

        Uses an anyio BlockingPortal and a queue to bridge between the async and sync worlds.
        This allows the executor to and present a synchronous iterator interface while leveraging async execution under
        the hood, avoid any issues with things like compute log capture that are not inherently async-aware or thread-safe.
        """
        event_queue: queue.Queue[DagsterEvent | _ErrorWrapper | object] = queue.Queue(
            maxsize=_SYNC_ASYNC_BRIDGE_QUEUE_MAXSIZE
        )

        compute_log_manager = job_context.instance.compute_log_manager
        step_keys = [s.key for s in execution_plan.get_steps_to_execute_in_topo_order()]
        file_key = create_compute_log_file_key()
        log_key = compute_log_manager.build_log_key_for_run(job_context.run_id, file_key)

        with (
            InstanceConcurrencyContext(
                job_context.instance, job_context.dagster_run
            ) as instance_concurrency_context,
            execution_plan.start(
                retry_mode=self.retries,
                max_concurrent=self._max_concurrent,
                tag_concurrency_limits=self._tag_concurrency_limits,
                instance_concurrency_context=instance_concurrency_context,
                step_dependency_config=self.step_dependency_config,
            ) as active,
            ExitStack() as capture_stack,
        ):
            # 1) Compute logs (still sync)
            try:
                log_context = capture_stack.enter_context(compute_log_manager.capture_logs(log_key))
                yield DagsterEvent.capture_logs(job_context, step_keys, log_key, log_context)
            except Exception:
                yield from _handle_compute_log_setup_error(job_context, sys.exc_info())

            # 2) Define async to sync bridge
            async def _async_iterator_to_queue() -> None:
                try:
                    async for i in self._async_execution_iterator(job_context, active):
                        event_queue.put(i)
                except BaseException as e:
                    event_queue.put(_ErrorWrapper(e))
                finally:
                    event_queue.put(_SENTINEL)

            # 3) Start the blocking portal and consume from the queue
            with start_blocking_portal() as portal:
                task = portal.start_task_soon(_async_iterator_to_queue)
                try:
                    while True:
                        item = event_queue.get()
                        if item is _SENTINEL:
                            break
                        if isinstance(item, _ErrorWrapper):
                            try:
                                task.cancel()
                            except BaseException:
                                pass
                            raise item.exc
                        assert isinstance(
                            item, DagsterEvent
                        )  # after narrowing, item must be DagsterEvent
                        yield item
                except BaseException:
                    try:
                        task.cancel()
                    except Exception:
                        pass
                    raise

    async def _async_execution_iterator(
        self,
        job_context: PlanExecutionContext,
        active: ActiveExecution,
    ) -> AsyncIterator[DagsterEvent]:
        """Async orchestrator that runs steps in a TaskGroup and yields events.

        - Uses a single anyio memory object stream as the central event bus.
        - Each step worker clones the send_stream and writes its events there.
        - We update ActiveExecution based on events and schedule new work as usual.
        """
        send_stream, recv_stream = anyio.create_memory_object_stream[DagsterEvent]()

        async with recv_stream, anyio.create_task_group() as tg:
            try:
                while not active.is_complete:
                    steps_to_execute = active.get_steps_to_execute(limit=None)

                    for event in active.concurrency_event_iterator(job_context):
                        yield event

                    known_state = active.get_known_state()
                    for step in steps_to_execute:
                        tg.start_soon(
                            self._run_step_worker,
                            job_context,
                            known_state,
                            step,
                            send_stream.clone(),
                        )

                    try:
                        event = await recv_stream.receive()
                    except anyio.EndOfStream:
                        raise

                    yield event
                    active.handle_event(event)
                    await _verify_if_complete(job_context, active, event)

                    for plan_event in active.plan_events_iterator(job_context):
                        yield plan_event
            finally:
                await send_stream.aclose()

            async for event in self._drain_events(active, job_context, recv_stream):
                yield event

    async def _run_step_worker(
        self,
        job_context: PlanExecutionContext,
        known_state: KnownExecutionState,
        step: ExecutionStep,
        send_stream: MemoryObjectSendStream[DagsterEvent],
    ) -> None:
        """Run a single step's async compute, emitting DagsterEvents via send_stream."""
        step_context = job_context.for_step(step, known_state)
        missing_resources = [
            resource_key
            for resource_key in step_context.required_resource_keys
            if not hasattr(step_context.resources, resource_key)
        ]
        check.invariant(
            len(missing_resources) == 0,
            (
                f"Expected step context for op {step_context.op.name} to have all required "
                f"resources, but missing {missing_resources}."
            ),
        )
        async with send_stream:
            try:
                step_events: list[DagsterEvent] = []
                async for event in dagster_event_sequence_for_step(step_context):
                    await send_stream.send(event)
                    step_events.append(event)

                async for hook_event in _trigger_hook(step_context, step_events):
                    await send_stream.send(hook_event)
            except BaseException:
                failure_event = step_failure_event_from_exc_info(
                    step_context,
                    sys.exc_info(),
                )
                try:
                    await send_stream.send(failure_event)
                finally:
                    raise

    async def _drain_events(
        self,
        active: ActiveExecution,
        job_context: PlanExecutionContext,
        recv_stream: MemoryObjectReceiveStream[DagsterEvent],
    ) -> AsyncIterator[DagsterEvent]:
        """Drain any remaining events from recv_stream after all steps complete."""
        while True:
            try:
                event = await recv_stream.receive()
            except anyio.EndOfStream:
                break
            yield event

            active.handle_event(event)
            await _verify_if_complete(job_context, active, event)

            for plan_event in active.plan_events_iterator(job_context):
                yield plan_event
