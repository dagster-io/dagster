from collections import defaultdict
from typing import Optional, Sequence

import pendulum

from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

from .instance import DagsterInstance
from .storage.dagster_run import DagsterRun, DagsterRunStatus, RunRecord
from .storage.tags import GLOBAL_CONCURRENCY_TAG


def compute_root_concurrency_keys_for_snapshot(
    plan_snapshot: ExecutionPlanSnapshot,
) -> Sequence[Optional[str]]:
    """Utility function called at run creation time to add the concurrency info needed to keep track
    of concurrency limits for each in-flight run.
    """
    root_step_keys = set(
        [step_key for step_key, deps in plan_snapshot.step_deps.items() if not deps]
    )
    return [
        (step.tags or {}).get(GLOBAL_CONCURRENCY_TAG)
        for step in plan_snapshot.steps
        if step.key in root_step_keys
    ]


class GlobalOpConcurrencyLimitsCounter:
    def __init__(
        self,
        instance: DagsterInstance,
        runs: Sequence[DagsterRun],
        in_progress_run_records: Sequence[RunRecord],
        slot_count_offset: int = 0,
        started_run_buffer_seconds: int = 0,
    ):
        self._root_concurrency_keys_by_run = {}
        self._concurrency_info_by_key = {}
        self._launched_concurrency_key_counts = defaultdict(int)
        self._in_progress_concurrency_key_counts = defaultdict(int)
        self._slot_count_offset = slot_count_offset
        self._started_run_buffer_seconds = started_run_buffer_seconds

        # fetch all the concurrency info for all of the runs at once, so we can claim in the correct
        # priority order
        self._fetch_concurrency_info(instance, runs)

        # fetch all the outstanding concurrency keys for in-progress runs
        self._process_in_progress_runs(in_progress_run_records)

    def _fetch_concurrency_info(self, instance: DagsterInstance, queued_runs: Sequence[DagsterRun]):
        # fetch all the concurrency slot information for the root concurrency keys of all the queued
        # runs
        all_concurrency_keys = set()
        for run in queued_runs:
            if not run.root_op_concurrency_keys:
                continue
            all_concurrency_keys.update([key for key in run.root_op_concurrency_keys if key])

        for key in all_concurrency_keys:
            self._concurrency_info_by_key[key] = instance.event_log_storage.get_concurrency_info(
                key
            )

    def _should_allocate_slots_for_root_concurrency_keys(self, record: RunRecord):
        status = record.dagster_run.status
        if status == DagsterRunStatus.STARTING:
            return True
        if status != DagsterRunStatus.STARTED or not record.start_time:
            return False
        time_elapsed = pendulum.now("UTC").timestamp() - record.start_time
        if time_elapsed < self._started_run_buffer_seconds:
            return True

    def _process_in_progress_runs(self, in_progress_records: Sequence[RunRecord]):
        for record in in_progress_records:
            if self._should_allocate_slots_for_root_concurrency_keys(record):
                concurrency_keys = record.dagster_run.root_op_concurrency_keys
                if not concurrency_keys:
                    continue
                for concurrency_key in concurrency_keys:
                    if concurrency_key:
                        self._in_progress_concurrency_key_counts[concurrency_key] += 1

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        root_concurrency_keys = run.root_op_concurrency_keys
        if not root_concurrency_keys or any(
            [not isinstance(key, str) for key in root_concurrency_keys]
        ):
            # if there exists a root node that is not concurrency blocked, we should dequeue
            return False

        for concurrency_key in root_concurrency_keys:
            if concurrency_key not in self._concurrency_info_by_key:
                # there is no concurrency limit set for this key, we should dequeue
                return False

            key_info = self._concurrency_info_by_key[concurrency_key]
            available_count = (
                key_info.slot_count
                - len(key_info.pending_steps)
                - self._launched_concurrency_key_counts[concurrency_key]
                - self._in_progress_concurrency_key_counts[concurrency_key]
            )
            if available_count > -1 * self._slot_count_offset:
                # there exists a root concurrency key that is not blocked, we should dequeue
                return False

        # if we reached here, then every root concurrency key is blocked, so we should not dequeue
        return True

    def update_counters_with_launched_item(self, run: DagsterRun):
        if not run.root_op_concurrency_keys:
            return
        for concurrency_key in run.root_op_concurrency_keys:
            if concurrency_key:
                self._launched_concurrency_key_counts[concurrency_key] += 1
