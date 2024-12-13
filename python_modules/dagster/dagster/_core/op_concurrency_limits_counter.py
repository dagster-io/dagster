import os
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Mapping, Optional, Sequence, Set

from dagster._core.instance import DagsterInstance
from dagster._core.run_coordinator.queued_run_coordinator import ConcurrencyGranularity
from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunOpConcurrency,
    RunRecord,
)
from dagster._time import get_current_timestamp

if TYPE_CHECKING:
    from dagster._utils.concurrency import ConcurrencyKeyInfo


def compute_run_op_concurrency_info_for_snapshot(
    plan_snapshot: ExecutionPlanSnapshot,
) -> Optional[RunOpConcurrency]:
    """Utility function called at run creation time to add the concurrency info needed to keep track
    of concurrency limits for each in-flight run.
    """
    root_step_keys = set(
        [step_key for step_key, deps in plan_snapshot.step_deps.items() if not deps]
    )
    root_concurrency_key_counts: Mapping[str, int] = defaultdict(int)
    all_concurrency_keys: Set[str] = set()
    has_unconstrained_root_nodes = False
    for step in plan_snapshot.steps:
        if step.concurrency_key is None and step.key in root_step_keys:
            has_unconstrained_root_nodes = True
        elif step.concurrency_key is None:
            continue
        elif step.key in root_step_keys:
            root_concurrency_key_counts[step.concurrency_key] += 1
            all_concurrency_keys.add(step.concurrency_key)
        else:
            all_concurrency_keys.add(step.concurrency_key)

    if len(all_concurrency_keys) == 0:
        return None

    return RunOpConcurrency(
        all_keys=all_concurrency_keys,
        root_key_counts=dict(root_concurrency_key_counts),
        has_unconstrained_root_nodes=has_unconstrained_root_nodes,
    )


class GlobalOpConcurrencyLimitsCounter:
    def __init__(
        self,
        instance: DagsterInstance,
        runs: Sequence[DagsterRun],
        in_progress_run_records: Sequence[RunRecord],
        slot_count_offset: int = 0,
        concurrency_group_granularity: ConcurrencyGranularity = ConcurrencyGranularity.OP,
    ):
        self._root_concurrency_keys_by_run = {}
        self._concurrency_info_by_key: Dict[str, "ConcurrencyKeyInfo"] = {}
        self._launched_concurrency_key_counts = defaultdict(int)
        self._in_progress_concurrency_key_counts = defaultdict(int)
        self._slot_count_offset = slot_count_offset
        self._concurrency_group_granularity = concurrency_group_granularity
        self._in_progress_run_ids: Set[str] = set(
            [record.dagster_run.run_id for record in in_progress_run_records]
        )
        self._started_run_concurrency_keys_allotted_seconds = int(
            os.getenv("DAGSTER_OP_CONCURRENCY_KEYS_ALLOTTED_FOR_STARTED_RUN_SECONDS", "5")
        )

        # fetch all the concurrency info for all of the runs at once, so we can claim in the correct
        # priority order
        self._fetch_concurrency_info(instance, runs)

        # fetch all the outstanding concurrency keys for in-progress runs
        self._process_in_progress_runs(in_progress_run_records)

    def _fetch_concurrency_info(self, instance: DagsterInstance, queued_runs: Sequence[DagsterRun]):
        # fetch all the concurrency slot information for all the queued runs
        all_concurrency_keys = set()

        configured_concurrency_keys = instance.event_log_storage.get_concurrency_keys()
        for run in queued_runs:
            if run.run_op_concurrency:
                # if using run granularity, consider all the concurrency keys required by the run
                # if using op granularity, consider only the root keys
                run_concurrency_keys = (
                    run.run_op_concurrency.root_key_counts.keys()
                    if self._concurrency_group_granularity == ConcurrencyGranularity.OP
                    else run.run_op_concurrency.all_keys or []
                )
                all_concurrency_keys.update(run_concurrency_keys)

        for key in all_concurrency_keys:
            if key is None:
                continue

            if key not in configured_concurrency_keys:
                instance.event_log_storage.initialize_concurrency_limit_to_default(key)

            self._concurrency_info_by_key[key] = instance.event_log_storage.get_concurrency_info(
                key
            )

    def _should_allocate_slots_for_in_progress_run(self, record: RunRecord):
        if not record.dagster_run.run_op_concurrency:
            return False

        status = record.dagster_run.status
        if status not in IN_PROGRESS_RUN_STATUSES:
            return False

        if self._concurrency_group_granularity == ConcurrencyGranularity.RUN:
            return True

        if status == DagsterRunStatus.STARTING:
            return True

        if status != DagsterRunStatus.STARTED or not record.start_time:
            return False

        time_elapsed = get_current_timestamp() - record.start_time
        if time_elapsed < self._started_run_concurrency_keys_allotted_seconds:
            return True

    def _slot_counts_for_run(self, run: DagsterRun) -> Mapping[str, int]:
        if not run.run_op_concurrency:
            return {}

        if self._concurrency_group_granularity == ConcurrencyGranularity.OP:
            return {**run.run_op_concurrency.root_key_counts}

        else:
            assert self._concurrency_group_granularity == ConcurrencyGranularity.RUN
            return {concurrency_key: 1 for concurrency_key in run.run_op_concurrency.all_keys or []}

    def _process_in_progress_runs(self, in_progress_records: Sequence[RunRecord]):
        for record in in_progress_records:
            if not self._should_allocate_slots_for_in_progress_run(record):
                continue

            for concurrency_key, count in self._slot_counts_for_run(record.dagster_run).items():
                self._in_progress_concurrency_key_counts[concurrency_key] += count

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        if not run.run_op_concurrency:
            return False

        if (
            self._concurrency_group_granularity == ConcurrencyGranularity.OP
            and run.run_op_concurrency.has_unconstrained_root_nodes
        ):
            # if the granularity is at the op level and there exists a root node that is not
            # concurrency blocked, we should dequeue.
            return False

        if self._concurrency_group_granularity == ConcurrencyGranularity.OP:
            # we just need to check all of the root concurrency keys, instead of all the concurrency keys
            # in the run
            for concurrency_key in run.run_op_concurrency.root_key_counts.keys():
                if concurrency_key not in self._concurrency_info_by_key:
                    # there is no concurrency limit set for this key, we should dequeue
                    return False

                key_info = self._concurrency_info_by_key[concurrency_key]
                unaccounted_occupied_slots = [
                    pending_step
                    for pending_step in key_info.pending_steps
                    if pending_step.run_id not in self._in_progress_run_ids
                ]
                available_count = (
                    key_info.slot_count
                    - len(unaccounted_occupied_slots)
                    - self._launched_concurrency_key_counts[concurrency_key]
                    - self._in_progress_concurrency_key_counts[concurrency_key]
                )
                if available_count + self._slot_count_offset > 0:
                    # there exists a root concurrency key that is not blocked, we should dequeue
                    return False

            # if we reached here, then every root concurrency key is blocked, so we should not dequeue
            return True

        else:
            assert self._concurrency_group_granularity == ConcurrencyGranularity.RUN

            # if the granularity is at the run level, we should check if any of the concurrency
            # keys are blocked
            for concurrency_key in run.run_op_concurrency.all_keys or []:
                if concurrency_key not in self._concurrency_info_by_key:
                    # there is no concurrency limit set for this key
                    continue

                key_info = self._concurrency_info_by_key[concurrency_key]
                unaccounted_occupied_slots = [
                    pending_step
                    for pending_step in key_info.pending_steps
                    if pending_step.run_id not in self._in_progress_run_ids
                ]
                available_count = (
                    key_info.slot_count
                    - len(unaccounted_occupied_slots)
                    - self._launched_concurrency_key_counts[concurrency_key]
                    - self._in_progress_concurrency_key_counts[concurrency_key]
                )
                if available_count + self._slot_count_offset <= 0:
                    return True

            # if we reached here then there is at least one available slot for every single concurrency key
            # required by this run, so we should dequeue
            return False

    def get_blocked_run_debug_info(self, run: DagsterRun) -> Mapping:
        if not run.run_op_concurrency:
            return {}

        log_info = {}
        for concurrency_key in run.run_op_concurrency.root_key_counts.keys():
            concurrency_info = self._concurrency_info_by_key.get(concurrency_key)
            if not concurrency_info:
                continue

            log_info[concurrency_key] = {
                "granularity": self._concurrency_group_granularity.value,
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
        for concurrency_key, count in self._slot_counts_for_run(run).items():
            self._launched_concurrency_key_counts[concurrency_key] += count
