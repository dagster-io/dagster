import json
from collections import defaultdict
from typing import Mapping, Optional, Sequence

import pendulum

from .instance import DagsterInstance
from .snap import JobSnapshot
from .storage.dagster_run import DagsterRun, DagsterRunStatus, RunRecord
from .storage.tags import (
    GLOBAL_CONCURRENCY_TAG,
    RUN_OP_ROOT_CONCURRENCY_KEYS,
)


def compute_concurrency_tags_for_snapshot(job_snapshot: JobSnapshot) -> Mapping[str, str]:
    """Utility function called at run creation time to tag each run with the concurrency info needed
    to keep track of concurrency limits for each in-flight run.
    """
    concurrency_keys_by_node_name = {
        node.node_name: node.tags.get(GLOBAL_CONCURRENCY_TAG)
        for node in job_snapshot.dep_structure_snapshot.node_invocation_snaps
        if node.tags.get(GLOBAL_CONCURRENCY_TAG)
    }
    if not concurrency_keys_by_node_name:
        return {}
    root_nodes = [
        node.node_name
        for node in job_snapshot.dep_structure_snapshot.node_invocation_snaps
        if not node.input_dep_snaps
    ]
    root_concurrency_keys = [
        concurrency_keys_by_node_name.get(node_name) for node_name in root_nodes
    ]
    return {
        RUN_OP_ROOT_CONCURRENCY_KEYS: json.dumps(root_concurrency_keys),
    }


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

    def _root_concurrency_keys_for_run(self, run: DagsterRun) -> Sequence[Optional[str]]:
        if run.run_id in self._root_concurrency_keys_by_run:
            return self._root_concurrency_keys_by_run[run.run_id]

        root_concurrency_keys_str = run.tags.get(RUN_OP_ROOT_CONCURRENCY_KEYS)
        if not root_concurrency_keys_str:
            self._root_concurrency_keys_by_run[run.run_id] = []
            return []
        try:
            keys = json.loads(root_concurrency_keys_str)
        except:
            keys = []
        self._root_concurrency_keys_by_run[run.run_id] = keys
        return keys

    def _fetch_concurrency_info(self, instance: DagsterInstance, queued_runs: Sequence[DagsterRun]):
        # fetch all the concurrency slot information for the root concurrency keys of all the queued
        # runs
        all_concurrency_keys = set()
        for run in queued_runs:
            root_concurrency_keys = self._root_concurrency_keys_for_run(run)
            all_concurrency_keys.update([key for key in root_concurrency_keys if key])

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
                for concurrency_key in self._root_concurrency_keys_for_run(record.dagster_run):
                    if concurrency_key:
                        self._in_progress_concurrency_key_counts[concurrency_key] += 1

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        root_concurrency_keys = self._root_concurrency_keys_for_run(run)
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
        for concurrency_key in self._root_concurrency_keys_for_run(run):
            if concurrency_key:
                self._launched_concurrency_key_counts[concurrency_key] += 1
