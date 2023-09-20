import time
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
    cast,
)

from typing_extensions import Self

import dagster._check as check
from dagster._core.errors import (
    DagsterExecutionInterruptedError,
    DagsterInvariantViolationError,
    DagsterUnknownStepStateError,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import (
    IPlanContext,
    PlanExecutionContext,
    PlanOrchestrationContext,
)
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode, RetryState
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG, PRIORITY_TAG
from dagster._utils.interrupts import pop_captured_interrupt
from dagster._utils.tags import TagConcurrencyLimitsCounter

from .instance_concurrency_context import InstanceConcurrencyContext
from .outputs import StepOutputData, StepOutputHandle
from .plan import ExecutionPlan
from .step import ExecutionStep


def _default_sort_key(step: ExecutionStep) -> float:
    return int(step.tags.get(PRIORITY_TAG, 0)) * -1


CONCURRENCY_CLAIM_BLOCKED_INTERVAL = 1


class ActiveExecution:
    """State machine used to track progress through execution of an ExecutionPlan."""

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        retry_mode: RetryMode,
        sort_key_fn: Optional[Callable[[ExecutionStep], float]] = None,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[List[Dict[str, Any]]] = None,
        instance_concurrency_context: Optional[InstanceConcurrencyContext] = None,
    ):
        self._plan: ExecutionPlan = check.inst_param(
            execution_plan, "execution_plan", ExecutionPlan
        )
        self._retry_mode = check.inst_param(retry_mode, "retry_mode", RetryMode)
        self._retry_state = self._plan.known_state.get_retry_state()
        self._instance_concurrency_context = instance_concurrency_context

        self._sort_key_fn: Callable[[ExecutionStep], float] = (
            check.opt_callable_param(
                sort_key_fn,
                "sort_key_fn",
            )
            or _default_sort_key
        )

        self._max_concurrent = check.opt_int_param(max_concurrent, "max_concurrent")
        self._tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits, "tag_concurrency_limits"
        )

        self._context_guard: bool = False  # Prevent accidental direct use

        # We decide what steps to skip based on what outputs are yielded by upstream steps
        self._step_outputs: Set[StepOutputHandle] = set(self._plan.known_state.ready_outputs)

        # All steps to be executed start out here in _pending
        self._pending: Dict[str, Set[str]] = dict(self._plan.get_executable_step_deps())

        # track mapping keys from DynamicOutputs, step_key, output_name -> list of keys
        # to _gathering while in flight
        self._gathering_dynamic_outputs: Dict[str, Mapping[str, Optional[List[str]]]] = {}
        # then on resolution move to _completed
        self._completed_dynamic_outputs: Dict[str, Mapping[str, Optional[Sequence[str]]]] = (
            dict(self._plan.known_state.dynamic_mappings) if self._plan.known_state else {}
        )
        self._new_dynamic_mappings: bool = False

        # track which upstream deps caused a step to skip
        self._skipped_deps: Dict[str, Sequence[str]] = {}

        # steps move in to these buckets as a result of _update calls
        self._executable: List[str] = []
        self._pending_skip: List[str] = []
        self._pending_retry: List[str] = []
        self._pending_abandon: List[str] = []
        self._waiting_to_retry: Dict[str, float] = {}

        # then are considered _in_flight when vended via get_steps_to_*
        self._in_flight: Set[str] = set()

        # and finally their terminal state is tracked by these sets, via mark_*
        self._success: Set[str] = set()
        self._failed: Set[str] = set()
        self._skipped: Set[str] = set()
        self._abandoned: Set[str] = set()

        # see verify_complete
        self._unknown_state: Set[str] = set()

        self._interrupted: bool = False

        # Start the show by loading _executable with the set of _pending steps that have no deps
        self._update()

    def __enter__(self) -> Self:
        self._context_guard = True
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self._context_guard = False

        # Exiting due to exception, return to allow exception to bubble
        if exc_type or exc_value or traceback:
            return

        if not self.is_complete:
            # generate the state string before exiting the concurrency context
            state_str = self._pending_state_str()
        else:
            state_str = ""

        if not self.is_complete:
            if self._interrupted:
                raise DagsterExecutionInterruptedError(
                    f"Execution was interrupted before completing the execution plan. {state_str}"
                )
            else:
                raise DagsterInvariantViolationError(
                    f"Execution finished without completing the execution plan. {state_str}"
                )

        # See verify_complete - steps for which we did not observe a failure/success event are in an unknown
        # state so we raise to ensure pipeline failure.
        if len(self._unknown_state) > 0:
            if self._interrupted:
                raise DagsterExecutionInterruptedError(
                    f"Execution exited with steps {self._unknown_state} in an unknown state after "
                    "being interrupted."
                )
            else:
                raise DagsterUnknownStepStateError(
                    f"Execution exited with steps {self._unknown_state} in an unknown state to this"
                    " process.\nThis was likely caused by losing communication with the process"
                    " performing step execution."
                )

    def _pending_state_str(self) -> str:
        assert not self.is_complete
        pending_action = (
            self._executable + self._pending_abandon + self._pending_retry + self._pending_skip
        )
        return "{pending_str}{in_flight_str}{action_str}{retry_str}{claim_str}".format(
            in_flight_str=f"\nSteps still in flight: {self._in_flight}" if self._in_flight else "",
            pending_str=(
                f"\nSteps pending processing: {self._pending.keys()}" if self._pending else ""
            ),
            action_str=f"\nSteps pending action: {pending_action}" if pending_action else "",
            retry_str=(
                f"\nSteps waiting to retry: {self._waiting_to_retry.keys()}"
                if self._waiting_to_retry
                else ""
            ),
            claim_str=(
                "\nSteps waiting to claim:"
                f" {self._instance_concurrency_context.pending_claim_steps()}"
                if self._instance_concurrency_context
                and self._instance_concurrency_context.has_pending_claims()
                else ""
            ),
        )

    def _update(self) -> None:
        """Moves steps from _pending to _executable / _pending_skip / _pending_retry
        as a function of what has been _completed.
        """
        new_steps_to_execute: List[str] = []
        new_steps_to_skip: List[str] = []
        new_steps_to_abandon: List[str] = []

        successful_or_skipped_steps = self._success | self._skipped
        failed_or_abandoned_steps = self._failed | self._abandoned

        if self._new_dynamic_mappings:
            new_step_deps = self._plan.resolve(self._completed_dynamic_outputs)
            for step_key, deps in new_step_deps.items():
                self._pending[step_key] = deps

            self._new_dynamic_mappings = False

        for step_key, requirements in self._pending.items():
            # If any upstream deps failed - this is not executable
            if requirements.intersection(failed_or_abandoned_steps):
                new_steps_to_abandon.append(step_key)

            # If all the upstream steps of a step are complete or skipped
            elif requirements.issubset(successful_or_skipped_steps):
                step = self.get_step_by_key(step_key)

                # The base case is downstream step won't skip
                should_skip = False

                # If there is at least one of the step's inputs, none of whose upstream steps has
                # yielded an output, we should skip that step.
                for step_input in step.step_inputs:
                    missing_source_handles = [
                        source_handle
                        for source_handle in step_input.get_step_output_handle_dependencies()
                        if source_handle.step_key in requirements
                        and source_handle not in self._step_outputs
                    ]
                    if missing_source_handles:
                        if len(missing_source_handles) == len(
                            step_input.get_step_output_handle_dependencies()
                        ):
                            should_skip = True
                            self._skipped_deps[step_key] = [
                                f"{h.step_key}.{h.output_name}" for h in missing_source_handles
                            ]
                            break

                if should_skip:
                    new_steps_to_skip.append(step_key)
                else:
                    new_steps_to_execute.append(step_key)

        for key in new_steps_to_execute:
            self._executable.append(key)
            del self._pending[key]

        for key in new_steps_to_skip:
            self._pending_skip.append(key)
            del self._pending[key]

        for key in new_steps_to_abandon:
            self._pending_abandon.append(key)
            del self._pending[key]

        ready_to_retry = []
        tick_time = time.time()
        for key, at_time in self._waiting_to_retry.items():
            if tick_time >= at_time:
                ready_to_retry.append(key)

        for key in ready_to_retry:
            self._executable.append(key)
            del self._waiting_to_retry[key]

    def sleep_interval(self):
        now = time.time()
        intervals = []
        if self._waiting_to_retry:
            for t in self._waiting_to_retry.values():
                intervals.append(t - now)
        if (
            self._instance_concurrency_context
            and self._instance_concurrency_context.has_pending_claims()
        ):
            intervals.append(
                self._instance_concurrency_context.interval_to_next_pending_claim_check()
            )
        if intervals:
            return min(intervals)

        return 0

    def sleep_til_ready(self) -> None:
        sleep_amt = self.sleep_interval()
        if sleep_amt > 0:
            time.sleep(sleep_amt)

    def get_next_step(self) -> Optional[ExecutionStep]:
        check.invariant(not self.is_complete, "Can not call get_next_step when is_complete is True")

        steps = self.get_steps_to_execute(limit=1)

        if not steps:
            return None

        return steps[0]

    def get_step_by_key(self, step_key: str) -> ExecutionStep:
        step = self._plan.get_step_by_key(step_key)
        return cast(ExecutionStep, check.inst(step, ExecutionStep))

    def get_steps_to_execute(
        self,
        limit: Optional[int] = None,
    ) -> Sequence[ExecutionStep]:
        check.invariant(
            self._context_guard,
            "ActiveExecution must be used as a context manager",
        )
        check.opt_int_param(limit, "limit")

        self._update()

        steps = sorted(
            [self.get_step_by_key(key) for key in self._executable],
            key=self._sort_key_fn,
        )

        run_scoped_concurrency_limits_counter = None
        if self._tag_concurrency_limits:
            in_flight_steps = [self.get_step_by_key(key) for key in self._in_flight]
            run_scoped_concurrency_limits_counter = TagConcurrencyLimitsCounter(
                self._tag_concurrency_limits,
                in_flight_steps,
            )

        batch: List[ExecutionStep] = []

        for step in steps:
            if limit is not None and len(batch) >= limit:
                break

            if (
                self._max_concurrent is not None
                and len(batch) + len(self._in_flight) >= self._max_concurrent
            ):
                break

            if run_scoped_concurrency_limits_counter:
                if run_scoped_concurrency_limits_counter.is_blocked(step):
                    continue

            if run_scoped_concurrency_limits_counter:
                run_scoped_concurrency_limits_counter.update_counters_with_launched_item(step)

            step_concurrency_key = step.tags.get(GLOBAL_CONCURRENCY_TAG)
            if step_concurrency_key and self._instance_concurrency_context:
                try:
                    priority = int(step.tags.get(PRIORITY_TAG, 0))
                except ValueError:
                    priority = 0

                if not self._instance_concurrency_context.claim(
                    step_concurrency_key, step.key, priority
                ):
                    continue

            batch.append(step)

        for step in batch:
            self._in_flight.add(step.key)
            self._executable.remove(step.key)
            self._prep_for_dynamic_outputs(step)

        return batch

    def get_steps_to_skip(self) -> Sequence[ExecutionStep]:
        self._update()

        steps = []
        steps_to_skip = list(self._pending_skip)
        for key in steps_to_skip:
            step = self.get_step_by_key(key)
            steps.append(step)
            self._in_flight.add(key)
            self._pending_skip.remove(key)
            self._gathering_dynamic_outputs  # noqa: B018
            self._skip_for_dynamic_outputs(step)

        return sorted(steps, key=self._sort_key_fn)

    def get_steps_to_abandon(self) -> Sequence[ExecutionStep]:
        self._update()

        steps = []
        steps_to_abandon = list(self._pending_abandon)
        for key in steps_to_abandon:
            steps.append(self.get_step_by_key(key))
            self._in_flight.add(key)
            self._pending_abandon.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def plan_events_iterator(
        self, job_context: Union[PlanExecutionContext, PlanOrchestrationContext]
    ) -> Iterator[DagsterEvent]:
        """Process all steps that can be skipped and abandoned."""
        steps_to_skip = self.get_steps_to_skip()
        while steps_to_skip:
            for step in steps_to_skip:
                step_context = job_context.for_step(step)
                step_context.log.info(
                    f"Skipping step {step.key} due to skipped dependencies:"
                    f" {self._skipped_deps[step.key]}."
                )
                yield DagsterEvent.step_skipped_event(step_context)

                self.mark_skipped(step.key)

            steps_to_skip = self.get_steps_to_skip()

        steps_to_abandon = self.get_steps_to_abandon()
        while steps_to_abandon:
            for step in steps_to_abandon:
                step_context = job_context.for_step(step)
                failed_inputs: List[str] = []
                for step_input in step.step_inputs:
                    failed_inputs.extend(self._failed.intersection(step_input.dependency_keys))

                abandoned_inputs: List[str] = []
                for step_input in step.step_inputs:
                    abandoned_inputs.extend(
                        self._abandoned.intersection(step_input.dependency_keys)
                    )

                step_context.log.error(
                    "Dependencies for step {step}{fail_str}{abandon_str}. Not executing.".format(
                        step=step.key,
                        fail_str=f" failed: {failed_inputs}" if failed_inputs else "",
                        abandon_str=(
                            f" were not executed: {abandoned_inputs}" if abandoned_inputs else ""
                        ),
                    )
                )
                self.mark_abandoned(step.key)

            steps_to_abandon = self.get_steps_to_abandon()

    def mark_failed(self, step_key: str) -> None:
        self._failed.add(step_key)
        self._mark_complete(step_key)

    def mark_success(self, step_key: str) -> None:
        self._success.add(step_key)
        self._mark_complete(step_key)
        self._resolve_any_dynamic_outputs(step_key)

    def mark_skipped(self, step_key: str) -> None:
        self._skipped.add(step_key)
        self._mark_complete(step_key)
        self._resolve_any_dynamic_outputs(step_key)

    def mark_abandoned(self, step_key: str) -> None:
        self._abandoned.add(step_key)
        self._mark_complete(step_key)

    def mark_interrupted(self) -> None:
        self._interrupted = True

    def check_for_interrupts(self) -> bool:
        return pop_captured_interrupt()

    def mark_up_for_retry(self, step_key: str, at_time: Optional[float] = None) -> None:
        check.invariant(
            not self._retry_mode.disabled,
            f"Attempted to mark {step_key} as up for retry but retries are disabled",
        )
        check.opt_float_param(at_time, "at_time")

        # if retries are enabled - queue this back up
        if self._retry_mode.enabled:
            if at_time:
                self._waiting_to_retry[step_key] = at_time
            else:
                self._pending[step_key] = self._plan.get_executable_step_deps()[step_key]

        elif self._retry_mode.deferred:
            # do not attempt to execute again
            self._abandoned.add(step_key)

        self._retry_state.mark_attempt(step_key)

        self._mark_complete(step_key)

    def _mark_complete(self, step_key: str) -> None:
        check.invariant(
            step_key in self._in_flight,
            f"Attempted to mark step {step_key} as complete that was not known to be in flight",
        )
        self._in_flight.remove(step_key)

    def handle_event(self, dagster_event: DagsterEvent) -> None:
        check.inst_param(dagster_event, "dagster_event", DagsterEvent)

        step_key = cast(str, dagster_event.step_key)
        if dagster_event.is_step_failure:
            self.mark_failed(step_key)
            if self._instance_concurrency_context:
                self._instance_concurrency_context.free_step(step_key)
        elif dagster_event.is_resource_init_failure:
            # Resources are only initialized without a step key in the
            # in-process case, and resource initalization happens before the
            # ActiveExecution object is created.
            check.invariant(
                dagster_event.step_key is not None,
                "Resource init failure was reported during execution without a step key.",
            )
            self.mark_failed(step_key)
            if self._instance_concurrency_context:
                self._instance_concurrency_context.free_step(step_key)
        elif dagster_event.is_step_success:
            self.mark_success(step_key)
            if self._instance_concurrency_context:
                self._instance_concurrency_context.free_step(step_key)
        elif dagster_event.is_step_skipped:
            # Skip events are generated by this class. They should not be sent via handle_event
            raise DagsterInvariantViolationError(
                f"Step {step_key} was reported as skipped from outside the ActiveExecution."
            )
        elif dagster_event.is_step_up_for_retry:
            self.mark_up_for_retry(
                step_key,
                (
                    time.time() + dagster_event.step_retry_data.seconds_to_wait
                    if dagster_event.step_retry_data.seconds_to_wait
                    else None
                ),
            )
        elif dagster_event.is_successful_output:
            event_specific_data = cast(StepOutputData, dagster_event.event_specific_data)
            self.mark_step_produced_output(event_specific_data.step_output_handle)
            if dagster_event.step_output_data.step_output_handle.mapping_key:
                check.not_none(
                    self._gathering_dynamic_outputs[step_key][
                        dagster_event.step_output_data.step_output_handle.output_name
                    ],
                ).append(dagster_event.step_output_data.step_output_handle.mapping_key)

    def verify_complete(self, job_context: IPlanContext, step_key: str) -> None:
        """Ensure that a step has reached a terminal state, if it has not mark it as an unexpected failure."""
        if step_key in self._in_flight:
            job_context.log.error(
                "Step {key} finished without success or failure event. Downstream steps will not"
                " execute.".format(key=step_key)
            )
            self.mark_unknown_state(step_key)

    # factored out for test
    def mark_unknown_state(self, step_key: str) -> None:
        # note the step so that we throw upon plan completion
        self._unknown_state.add(step_key)
        # mark as abandoned so downstream tasks do not execute
        self.mark_abandoned(step_key)

    # factored out for test
    def mark_step_produced_output(self, step_output_handle: StepOutputHandle) -> None:
        self._step_outputs.add(step_output_handle)

    @property
    def is_complete(self) -> bool:
        return (
            len(self._pending) == 0
            and len(self._in_flight) == 0
            and len(self._executable) == 0
            and len(self._pending_skip) == 0
            and len(self._pending_retry) == 0
            and len(self._pending_abandon) == 0
            and len(self._waiting_to_retry) == 0
            and (
                not self._instance_concurrency_context
                or not self._instance_concurrency_context.has_pending_claims()
            )
        )

    @property
    def retry_state(self) -> RetryState:
        return self._retry_state

    def get_known_state(self) -> KnownExecutionState:
        return KnownExecutionState(
            previous_retry_attempts=self._retry_state.snapshot_attempts(),
            dynamic_mappings=dict(self._completed_dynamic_outputs),
            ready_outputs=self._step_outputs,
            step_output_versions=self._plan.known_state.step_output_versions,
            parent_state=self._plan.known_state.parent_state,
        )

    def _prep_for_dynamic_outputs(self, step: ExecutionStep):
        dyn_outputs = [step_out for step_out in step.step_outputs if step_out.is_dynamic]
        if dyn_outputs:
            self._gathering_dynamic_outputs[step.key] = {out.name: [] for out in dyn_outputs}

    def _skip_for_dynamic_outputs(self, step: ExecutionStep):
        dyn_outputs = [step_out for step_out in step.step_outputs if step_out.is_dynamic]
        if dyn_outputs:
            # place None to indicate the dynamic output was skipped, different than having 0 entries
            self._gathering_dynamic_outputs[step.key] = {out.name: None for out in dyn_outputs}

    def _resolve_any_dynamic_outputs(self, step_key: str) -> None:
        if step_key in self._gathering_dynamic_outputs:
            step = self.get_step_by_key(step_key)
            completed_mappings: Dict[str, Optional[Sequence[str]]] = {}
            for output_name, mappings in self._gathering_dynamic_outputs[step_key].items():
                # if no dynamic outputs were returned and the output was marked is_required=False
                # set to None to indicate a skip should occur
                if not mappings and not step.step_output_dict[output_name].is_required:
                    completed_mappings[output_name] = None
                else:
                    completed_mappings[output_name] = mappings

            self._completed_dynamic_outputs[step_key] = completed_mappings
            self._new_dynamic_mappings = True

    def rebuild_from_events(
        self, dagster_events: Sequence[DagsterEvent]
    ) -> Sequence[ExecutionStep]:
        """Replay events to rebuild the execution state and continue after a failure.

        Returns a list of steps that are possibly in flight. Current status of the event log implies
        that the previous run worker might have crashed before launching these steps, or it may have
        launched them but they have yet to report a STEP_START event.
        """
        self.get_steps_to_execute()

        for event in dagster_events:
            self.handle_event(event)
            self.get_steps_to_execute()

        return [self.get_step_by_key(step_key) for step_key in self._in_flight]
