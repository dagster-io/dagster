import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Optional

from dagster._core.instance import DagsterInstance
from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    RunOpConcurrency,
    RunRecord,
)
from dagster._time import get_current_timestamp


def compute_run_op_concurrency_info_for_snapshot(
    plan_snapshot: ExecutionPlanSnapshot,
) -> Optional[RunOpConcurrency]:
    """Utility function called at run creation time to add the concurrency info needed to keep track
    of concurrency limits for each in-flight run.
    """
    root_step_keys = set(
        [step_key for step_key, deps in plan_snapshot.step_deps.items() if not deps]
    )
    pool_counts: Mapping[str, int] = defaultdict(int)
    has_unconstrained_root_nodes = False
    for step in plan_snapshot.steps:
        if step.key not in root_step_keys:
            continue
        if step.pool is None:
            has_unconstrained_root_nodes = True
        else:
            pool_counts[step.pool] += 1

    if len(pool_counts) == 0:
        return None

    return RunOpConcurrency(
        root_key_counts=dict(pool_counts),
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
        self._root_pools_by_run = {}
        self._concurrency_info_by_pool = {}
        self._launched_pool_counts = defaultdict(int)
        self._in_progress_pool_counts = defaultdict(int)
        self._slot_count_offset = slot_count_offset
        self._in_progress_run_ids: set[str] = set(
            [record.dagster_run.run_id for record in in_progress_run_records]
        )
        self._started_run_pools_allotted_seconds = int(
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
        all_run_pools = set()

        configured_pools = instance.event_log_storage.get_concurrency_keys()
        for run in queued_runs:
            if run.run_op_concurrency:
                all_run_pools.update(run.run_op_concurrency.root_key_counts.keys())

        for key in all_run_pools:
            if key is None:
                continue

            if key not in configured_pools:
                instance.event_log_storage.initialize_concurrency_limit_to_default(key)

            self._concurrency_info_by_pool[key] = instance.event_log_storage.get_concurrency_info(
                key
            )

    def _should_allocate_slots_for_root_pools(self, record: RunRecord):
        status = record.dagster_run.status
        if status == DagsterRunStatus.STARTING:
            return True
        if status != DagsterRunStatus.STARTED or not record.start_time:
            return False
        time_elapsed = get_current_timestamp() - record.start_time
        if time_elapsed < self._started_run_pools_allotted_seconds:
            return True

    def _process_in_progress_runs(self, in_progress_records: Sequence[RunRecord]):
        for record in in_progress_records:
            if (
                self._should_allocate_slots_for_root_pools(record)
                and record.dagster_run.run_op_concurrency
            ):
                for (
                    pool,
                    count,
                ) in record.dagster_run.run_op_concurrency.root_key_counts.items():
                    self._in_progress_pool_counts[pool] += count

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        if not run.run_op_concurrency or run.run_op_concurrency.has_unconstrained_root_nodes:
            # if there exists a root node that is not concurrency blocked, we should dequeue.
            return False

        for pool in run.run_op_concurrency.root_key_counts.keys():
            if pool not in self._concurrency_info_by_pool:
                # there is no concurrency limit set for this key, we should dequeue
                return False

            key_info = self._concurrency_info_by_pool[pool]
            available_count = (
                key_info.slot_count
                - len(key_info.pending_steps)
                - self._launched_pool_counts[pool]
                - self._in_progress_pool_counts[pool]
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
        for pool in run.run_op_concurrency.root_key_counts.keys():
            concurrency_info = self._concurrency_info_by_pool.get(pool)
            if not concurrency_info:
                continue

            log_info[pool] = {
                "slot_count": concurrency_info.slot_count,
                "pending_step_count": len(concurrency_info.pending_steps),
                "pending_step_run_ids": list(
                    {step.run_id for step in concurrency_info.pending_steps}
                ),
                "launched_count": self._launched_pool_counts[pool],
                "in_progress_count": self._in_progress_pool_counts[pool],
            }
        return log_info

    def update_counters_with_launched_item(self, run: DagsterRun):
        if not run.run_op_concurrency:
            return
        for pool, count in run.run_op_concurrency.root_key_counts.items():
            if pool:
                self._launched_pool_counts[pool] += count
