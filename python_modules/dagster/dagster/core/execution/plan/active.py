import time
from collections import defaultdict
from typing import Callable, Dict, Iterator, List, Optional, Set, cast

from dagster import check
from dagster.core.errors import (
    DagsterExecutionInterruptedError,
    DagsterInvariantViolationError,
    DagsterUnknownStepStateError,
)
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.retries import Retries
from dagster.core.storage.tags import PRIORITY_TAG
from dagster.utils.interrupts import pop_captured_interrupt

from .outputs import StepOutputHandle
from .plan import ExecutionPlan
from .step import ExecutionStep


def _default_sort_key(step: ExecutionStep) -> float:
    return int(step.tags.get(PRIORITY_TAG, 0)) * -1


class ActiveExecution:
    """State machine used to track progress through execution of an ExecutionPlan"""

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        retries: Retries,
        sort_key_fn: Optional[Callable[[ExecutionStep], float]] = None,
    ):
        self._plan: ExecutionPlan = check.inst_param(
            execution_plan, "execution_plan", ExecutionPlan
        )
        self._retries: Retries = check.inst_param(retries, "retries", Retries)
        self._sort_key_fn: Callable[[ExecutionStep], float] = (
            check.opt_callable_param(
                sort_key_fn,
                "sort_key_fn",
            )
            or _default_sort_key
        )

        self._context_guard: bool = False  # Prevent accidental direct use

        # We decide what steps to skip based on what outputs are yielded by upstream steps
        self._step_outputs: Set[StepOutputHandle] = set()

        # All steps to be executed start out here in _pending
        self._pending: Dict[str, Set[str]] = self._plan.get_executable_step_deps()

        # track mapping keys from DynamicOutputs, step_key, output_name -> list of keys
        self._successful_dynamic_outputs: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # steps move in to these buckets as a result of _update calls
        self._executable: List[str] = []
        self._pending_skip: List[str] = []
        self._pending_retry: List[str] = []
        self._pending_abandon: List[str] = []
        self._pending_resolve: List[str] = []
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

    def __enter__(self):
        self._context_guard = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._context_guard = False

        # Exiting due to exception, return to allow exception to bubble
        if exc_type or exc_value or traceback:
            return

        if not self.is_complete:
            pending_action = (
                self._executable + self._pending_abandon + self._pending_retry + self._pending_skip
            )
            raise DagsterInvariantViolationError(
                "Execution of pipeline finished without completing the execution plan,."
                "{pending_str}{in_flight_str}{action_str}{retry_str}".format(
                    in_flight_str="\nSteps still in flight: {}".format(self._in_flight)
                    if self._in_flight
                    else "",
                    pending_str="\nSteps pending processing: {}".format(self._pending.keys())
                    if self._pending
                    else "",
                    action_str="\nSteps pending action: {}".format(pending_action)
                    if pending_action
                    else "",
                    retry_str="\nSteps waiting to retry: {}".format(self._waiting_to_retry.keys())
                    if self._waiting_to_retry
                    else "",
                )
            )

        # See verify_complete - steps for which we did not observe a failure/success event are in an unknown
        # state so we raise to ensure pipeline failure.
        if len(self._unknown_state) > 0:
            if self._interrupted:
                raise DagsterExecutionInterruptedError(
                    "Execution of pipeline exited with steps {step_list} in an unknown state after "
                    "being interrupted.".format(step_list=self._unknown_state)
                )
            else:
                raise DagsterUnknownStepStateError(
                    "Execution of pipeline exited with steps {step_list} in an unknown state to this process.\n"
                    "This was likely caused by losing communication with the process performing step execution.".format(
                        step_list=self._unknown_state
                    )
                )

    def _update(self) -> None:
        """Moves steps from _pending to _executable / _pending_skip / _pending_retry
        as a function of what has been _completed
        """
        new_steps_to_execute = []
        new_steps_to_skip = []
        new_steps_to_abandon = []

        successful_or_skipped_steps = self._success | self._skipped
        failed_or_abandoned_steps = self._failed | self._abandoned

        # make a copy since we are mutating during iteration
        pending_resolve_snapshot = list(self._pending_resolve)
        for idx, key in enumerate(pending_resolve_snapshot):
            new_step_deps = self._plan.resolve(key, self._successful_dynamic_outputs[key])
            for step_key, deps in new_step_deps.items():
                # does this work right with step_keys_to_execute?
                self._pending[step_key] = deps

            del self._pending_resolve[idx]

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

    def sleep_til_ready(self) -> None:
        now = time.time()
        sleep_amt = min([ready_at - now for ready_at in self._waiting_to_retry.values()])
        if sleep_amt > 0:
            time.sleep(sleep_amt)

    def get_next_step(self) -> ExecutionStep:
        check.invariant(not self.is_complete, "Can not call get_next_step when is_complete is True")

        steps = self.get_steps_to_execute(limit=1)
        step = None

        if steps:
            step = steps[0]
        elif self._waiting_to_retry:
            self.sleep_til_ready()
            step = self.get_next_step()

        check.invariant(step is not None, "Unexpected ActiveExecution state")
        return cast(ExecutionStep, step)

    def get_step_by_key(self, step_key: str) -> ExecutionStep:
        step = self._plan.get_step_by_key(step_key)
        return cast(ExecutionStep, check.inst(step, ExecutionStep))

    def get_steps_to_execute(self, limit: int = None) -> List[ExecutionStep]:
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

        if limit:
            steps = steps[:limit]

        for step in steps:
            self._in_flight.add(step.key)
            self._executable.remove(step.key)
        return steps

    def get_steps_to_skip(self) -> List[ExecutionStep]:
        self._update()

        steps = []
        steps_to_skip = list(self._pending_skip)
        for key in steps_to_skip:
            steps.append(self.get_step_by_key(key))
            self._in_flight.add(key)
            self._pending_skip.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def get_steps_to_abandon(self) -> List[ExecutionStep]:
        self._update()

        steps = []
        steps_to_abandon = list(self._pending_abandon)
        for key in steps_to_abandon:
            steps.append(self.get_step_by_key(key))
            self._in_flight.add(key)
            self._pending_abandon.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def plan_events_iterator(self, pipeline_context) -> Iterator[DagsterEvent]:
        """Process all steps that can be skipped and abandoned"""

        steps_to_skip = self.get_steps_to_skip()
        while steps_to_skip:
            for step in steps_to_skip:
                step_context = pipeline_context.for_step(step)
                skipped_inputs: List[str] = []
                for step_input in step.step_inputs:
                    skipped_inputs.extend(self._skipped.intersection(step_input.dependency_keys))

                step_context.log.info(
                    "Skipping step {step} due to skipped dependencies: {skipped_inputs}.".format(
                        step=step.key, skipped_inputs=skipped_inputs
                    )
                )
                yield DagsterEvent.step_skipped_event(step_context)

                self.mark_skipped(step.key)

            steps_to_skip = self.get_steps_to_skip()

        steps_to_abandon = self.get_steps_to_abandon()
        while steps_to_abandon:
            for step in steps_to_abandon:
                step_context = pipeline_context.for_step(step)
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
                        fail_str=" failed: {}".format(failed_inputs) if failed_inputs else "",
                        abandon_str=" were not executed: {}".format(abandoned_inputs)
                        if abandoned_inputs
                        else "",
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
        if step_key in self._successful_dynamic_outputs:
            self._pending_resolve.append(step_key)

    def mark_skipped(self, step_key: str) -> None:
        self._skipped.add(step_key)
        self._mark_complete(step_key)

    def mark_abandoned(self, step_key: str) -> None:
        self._abandoned.add(step_key)
        self._mark_complete(step_key)

    def mark_interrupted(self) -> None:
        self._interrupted = True

    def check_for_interrupts(self) -> None:
        return pop_captured_interrupt()

    def mark_up_for_retry(self, step_key: str, at_time: Optional[float] = None) -> None:
        check.invariant(
            not self._retries.disabled,
            "Attempted to mark {} as up for retry but retries are disabled".format(step_key),
        )
        check.opt_float_param(at_time, "at_time")

        # if retries are enabled - queue this back up
        if self._retries.enabled:
            if at_time:
                self._waiting_to_retry[step_key] = at_time
            else:
                self._pending[step_key] = self._plan.get_executable_step_deps()[step_key]

        elif self._retries.deferred:
            # do not attempt to execute again
            self._abandoned.add(step_key)

        self._retries.mark_attempt(step_key)

        self._mark_complete(step_key)

    def _mark_complete(self, step_key: str) -> None:
        check.invariant(
            step_key in self._in_flight,
            "Attempted to mark step {} as complete that was not known to be in flight".format(
                step_key
            ),
        )
        self._in_flight.remove(step_key)

    def handle_event(self, dagster_event: DagsterEvent) -> None:
        check.inst_param(dagster_event, "dagster_event", DagsterEvent)

        if dagster_event.is_step_failure:
            self.mark_failed(dagster_event.step_key)
        elif dagster_event.is_step_success:
            self.mark_success(dagster_event.step_key)
        elif dagster_event.is_step_skipped:
            self.mark_skipped(dagster_event.step_key)
        elif dagster_event.is_step_up_for_retry:
            self.mark_up_for_retry(
                dagster_event.step_key,
                time.time() + dagster_event.step_retry_data.seconds_to_wait
                if dagster_event.step_retry_data.seconds_to_wait
                else None,
            )
        elif dagster_event.is_successful_output:
            self.mark_step_produced_output(dagster_event.event_specific_data.step_output_handle)
            if dagster_event.step_output_data.step_output_handle.mapping_key:
                self._successful_dynamic_outputs[dagster_event.step_key][
                    dagster_event.step_output_data.step_output_handle.output_name
                ].append(dagster_event.step_output_data.step_output_handle.mapping_key)

    def verify_complete(
        self, pipeline_context: SystemPipelineExecutionContext, step_key: str
    ) -> None:
        """Ensure that a step has reached a terminal state, if it has not mark it as an unexpected failure"""
        if step_key in self._in_flight:
            pipeline_context.log.error(
                "Step {key} finished without success or failure event. Downstream steps will not execute.".format(
                    key=step_key
                )
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
        )
