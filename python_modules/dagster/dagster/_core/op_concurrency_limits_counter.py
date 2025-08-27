import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.instance import DagsterInstance
from dagster._core.instance.config import PoolGranularity
from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot, ExecutionStepSnap
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunOpConcurrency,
    RunRecord,
)
from dagster._core.storage.event_log.base import PoolLimit
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG
from dagster._time import get_current_timestamp

if TYPE_CHECKING:
    from dagster._utils.concurrency import ConcurrencyKeyInfo


def _pool_key_for_step(step: ExecutionStepSnap) -> Optional[str]:
    if step.pool is not None:
        return step.pool

    # for backwards compatibility, we also check the tags
    return (step.tags or {}).get(GLOBAL_CONCURRENCY_TAG)


def compute_run_op_concurrency_info_for_snapshot(
    plan_snapshot: ExecutionPlanSnapshot,
) -> Optional[RunOpConcurrency]:
    """Utility function called at run creation time to add the concurrency info needed to keep track
    of concurrency limits for each in-flight run.
    """
    step_keys_to_execute = set(plan_snapshot.step_keys_to_execute)
    root_step_keys = set(
        [
            step_key
            for step_key, deps in plan_snapshot.step_deps.items()
            if not deps.intersection(step_keys_to_execute)
        ]
    )
    root_key_counts: Mapping[str, int] = defaultdict(int)
    all_pools: set[str] = set()
    has_unconstrained_root_nodes = False
    for step in plan_snapshot.steps:
        if step.key not in step_keys_to_execute:
            continue

        step_pool = _pool_key_for_step(step)
        if step_pool is None and step.key in root_step_keys:
            has_unconstrained_root_nodes = True
        elif step_pool is None:
            continue
        elif step.key in root_step_keys:
            root_key_counts[step_pool] += 1
            if step_pool is not None:
                all_pools.add(step_pool)
        else:
            if step_pool is not None:
                all_pools.add(step_pool)

    if len(all_pools) == 0:
        return None

    return RunOpConcurrency(
        all_pools=all_pools,
        root_key_counts=dict(root_key_counts),
        has_unconstrained_root_nodes=has_unconstrained_root_nodes,
    )


class GlobalOpConcurrencyLimitsCounter:
    def __init__(
        self,
        instance: DagsterInstance,
        runs: Sequence[DagsterRun],
        in_progress_run_records: Sequence[RunRecord],
        concurrency_keys: set[str],
        pool_limits: Sequence[PoolLimit],
        slot_count_offset: int = 0,
        pool_granularity: Optional[PoolGranularity] = None,
    ):
        self._root_pools_by_run = {}
        self._concurrency_info_by_key: dict[str, ConcurrencyKeyInfo] = {}
        self._launched_pool_counts = defaultdict(int)
        self._in_progress_pool_counts = defaultdict(int)
        self._slot_count_offset = slot_count_offset
        self._pool_granularity = pool_granularity if pool_granularity else PoolGranularity.OP
        self._in_progress_run_ids: set[str] = set(
            [record.dagster_run.run_id for record in in_progress_run_records]
        )
        self._started_run_pools_allotted_seconds = int(
            os.getenv("DAGSTER_OP_CONCURRENCY_KEYS_ALLOTTED_FOR_STARTED_RUN_SECONDS", "5")
        )

        queued_pool_names = self._get_queued_pool_names(runs)
        # initialize all the pool limits to the default if necessary
        self._initialize_pool_limits(instance, queued_pool_names, pool_limits)

        # fetch all the configured pool keys
        all_configured_pool_names = concurrency_keys
        configured_queued_pool_names = all_configured_pool_names.intersection(queued_pool_names)

        # fetch all the concurrency info for all of the runs at once, so we can claim in the correct
        # priority order
        self._fetch_concurrency_info(instance, configured_queued_pool_names)

        # fetch all the outstanding pools for in-progress runs
        self._process_in_progress_runs(in_progress_run_records)

    def _get_queued_pool_names(self, queued_runs: Sequence[DagsterRun]) -> set[str]:
        queued_pool_names = set()
        for run in queued_runs:
            if run.run_op_concurrency:
                # if using run granularity, consider all the concurrency keys required by the run
                # if using op granularity, consider only the root keys
                run_pools = (
                    run.run_op_concurrency.root_key_counts.keys()
                    if self._pool_granularity == PoolGranularity.OP
                    else run.run_op_concurrency.all_pools or []
                )
                queued_pool_names.update(run_pools)
        return queued_pool_names

    def _initialize_pool_limits(
        self, instance: DagsterInstance, pool_names: set[str], pool_limits: Sequence[PoolLimit]
    ):
        default_limit = instance.global_op_concurrency_default_limit
        pool_limits_by_name = {pool.name: pool for pool in pool_limits}
        for pool_name in pool_names:
            if pool_name is None:
                continue

            if (pool_name not in pool_limits_by_name and default_limit) or (
                pool_name in pool_limits_by_name
                and pool_limits_by_name[pool_name].from_default
                and pool_limits_by_name[pool_name].limit != default_limit
            ):
                instance.event_log_storage.initialize_concurrency_limit_to_default(pool_name)

    def _fetch_concurrency_info(self, instance: DagsterInstance, pool_names: set[str]):
        for pool_name in pool_names:
            if pool_name is None:
                continue

            self._concurrency_info_by_key[pool_name] = (
                instance.event_log_storage.get_concurrency_info(pool_name)
            )

    def _should_allocate_slots_for_in_progress_run(self, record: RunRecord):
        if not record.dagster_run.run_op_concurrency:
            return False

        status = record.dagster_run.status
        if status not in IN_PROGRESS_RUN_STATUSES:
            return False

        if self._pool_granularity == PoolGranularity.RUN:
            return True

        if status == DagsterRunStatus.STARTING:
            return True

        if status != DagsterRunStatus.STARTED or not record.start_time:
            return False

        time_elapsed = get_current_timestamp() - record.start_time
        if time_elapsed < self._started_run_pools_allotted_seconds:
            return True

        return False

    def _slot_counts_for_run(self, run: DagsterRun) -> Mapping[str, int]:
        if not run.run_op_concurrency:
            return {}

        if self._pool_granularity == PoolGranularity.OP:
            return {**run.run_op_concurrency.root_key_counts}
        elif self._pool_granularity == PoolGranularity.RUN:
            return {pool: 1 for pool in run.run_op_concurrency.all_pools or []}
        else:
            check.failed(f"Unexpected pool granularity {self._pool_granularity}")

    def _process_in_progress_runs(self, in_progress_records: Sequence[RunRecord]):
        for record in in_progress_records:
            if not self._should_allocate_slots_for_in_progress_run(record):
                continue

            for pool, count in self._slot_counts_for_run(record.dagster_run).items():
                self._in_progress_pool_counts[pool] += count

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        if not run.run_op_concurrency:
            return False

        if (
            self._pool_granularity == PoolGranularity.OP
            and run.run_op_concurrency.has_unconstrained_root_nodes
        ):
            # if the granularity is at the op level and there exists a root node that is not
            # concurrency blocked, we should dequeue.
            return False

        if self._pool_granularity == PoolGranularity.OP:
            # we just need to check all of the root concurrency keys, instead of all the concurrency keys
            # in the run
            for pool in run.run_op_concurrency.root_key_counts.keys():
                if pool not in self._concurrency_info_by_key:
                    # there is no concurrency limit set for this key, we should dequeue
                    return False

                key_info = self._concurrency_info_by_key[pool]
                available_count = (
                    key_info.slot_count
                    - len(key_info.pending_steps)
                    - self._launched_pool_counts[pool]
                    - self._in_progress_pool_counts[pool]
                )
                if available_count + self._slot_count_offset > 0:
                    # there exists a root concurrency key that is not blocked, we should dequeue
                    return False

            # if we reached here, then every root concurrency key is blocked, so we should not dequeue
            return True

        elif self._pool_granularity == PoolGranularity.RUN:
            # if the granularity is at the run level, we should check if any of the concurrency
            # keys are blocked
            for pool in run.run_op_concurrency.all_pools or []:
                if pool not in self._concurrency_info_by_key:
                    # there is no concurrency limit set for this key
                    continue

                key_info = self._concurrency_info_by_key[pool]
                available_count = (
                    key_info.slot_count
                    - self._launched_pool_counts[pool]
                    - self._in_progress_pool_counts[pool]
                )
                if available_count + self._slot_count_offset <= 0:
                    return True

            # if we reached here then there is at least one available slot for every single concurrency key
            # required by this run, so we should dequeue
            return False
        else:
            check.failed(f"Unexpected pool granularity {self._pool_granularity}")

    def get_blocked_run_debug_info(self, run: DagsterRun) -> Mapping:
        if not run.run_op_concurrency:
            return {}

        log_info = {}
        for pool in run.run_op_concurrency.root_key_counts.keys():
            concurrency_info = self._concurrency_info_by_key.get(pool)
            if not concurrency_info:
                continue

            log_info[pool] = {
                "granularity": self._pool_granularity.value,
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
        for pool, count in self._slot_counts_for_run(run).items():
            self._launched_pool_counts[pool] += count
