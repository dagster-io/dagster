import os
from collections import defaultdict
from typing import Mapping, Optional, Sequence

import pendulum

from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

from .instance import DagsterInstance
from .storage.dagster_run import DagsterRun, DagsterRunStatus, RunOpConcurrency, RunRecord
from .storage.tags import GLOBAL_CONCURRENCY_TAG


def compute_run_op_concurrency_info_for_snapshot(
    plan_snapshot: ExecutionPlanSnapshot,
) -> Optional[RunOpConcurrency]:
    """Utility function called at run creation time to add the concurrency info needed to keep track
    of concurrency limits for each in-flight run.
    """
    root_step_keys = set(
        [step_key for step_key, deps in plan_snapshot.step_deps.items() if not deps]
    )
    concurrency_key_counts: Mapping[str, int] = defaultdict(int)
    has_unconstrained_root_nodes = False
    for step in plan_snapshot.steps:
        if step.key not in root_step_keys:
            continue
        concurrency_key = step.tags.get(GLOBAL_CONCURRENCY_TAG) if step.tags else None
        if concurrency_key is None:
            has_unconstrained_root_nodes = True
        else:
            concurrency_key_counts[concurrency_key] += 1

    if len(concurrency_key_counts) == 0:
        return None

    return RunOpConcurrency(
        root_key_counts=dict(concurrency_key_counts),
        has_unconstrained_root_nodes=has_unconstrained_root_nodes,
    )


class GlobalOpConcurrencyLimitsCounter:
    def __init__(
        self,
        instance: DagsterInstance,
        runs: Sequence[DagsterRun],
        in_progress_run_records: Sequence[RunRecord],
        slot_count_offset: int = 0,
    ):
        self._root_concurrency_keys_by_run = {}
        self._concurrency_info_by_key = {}
        self._launched_concurrency_key_counts = defaultdict(int)
        self._in_progress_concurrency_key_counts = defaultdict(int)
        self._slot_count_offset = slot_count_offset
        self._started_run_concurrency_keys_allotted_seconds = int(
            os.getenv("DAGSTER_OP_CONCURRENCY_KEYS_ALLOTTED_FOR_STARTED_RUN_SECONDS", "5")
        )

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
            if run.run_op_concurrency:
                all_concurrency_keys.update(run.run_op_concurrency.root_key_counts.keys())

        for key in all_concurrency_keys:
            if key is None:
                continue
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
        if time_elapsed < self._started_run_concurrency_keys_allotted_seconds:
            return True

    def _process_in_progress_runs(self, in_progress_records: Sequence[RunRecord]):
        for record in in_progress_records:
            if (
                self._should_allocate_slots_for_root_concurrency_keys(record)
                and record.dagster_run.run_op_concurrency
            ):
                for (
                    concurrency_key,
                    count,
                ) in record.dagster_run.run_op_concurrency.root_key_counts.items():
                    self._in_progress_concurrency_key_counts[concurrency_key] += count

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        if not run.run_op_concurrency or run.run_op_concurrency.has_unconstrained_root_nodes:
            # if there exists a root node that is not concurrency blocked, we should dequeue.
            return False

        for concurrency_key in run.run_op_concurrency.root_key_counts.keys():
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

    def get_blocked_run_debug_info(self, run: DagsterRun) -> Mapping:
        if not run.run_op_concurrency:
            return {}

        log_info = {}
        for concurrency_key in run.run_op_concurrency.root_key_counts.keys():
            concurrency_info = self._concurrency_info_by_key.get(concurrency_key)
            if not concurrency_info:
                continue

            log_info[concurrency_key] = {
                "slot_count": concurrency_info.slot_count,
                "pending_step_count": len(concurrency_info.pending_steps),
                "pending_step_run_ids": list(
                    {step.run_id for step in concurrency_info.pending_steps}
                ),
                "launched_count": self._launched_concurrency_key_counts[concurrency_key],
                "in_progress_count": self._in_progress_concurrency_key_counts[concurrency_key],
            }
        return log_info

    def update_counters_with_launched_item(self, run: DagsterRun):
        if not run.run_op_concurrency:
            return
        for concurrency_key, count in run.run_op_concurrency.root_key_counts.items():
            if concurrency_key:
                self._launched_concurrency_key_counts[concurrency_key] += count
