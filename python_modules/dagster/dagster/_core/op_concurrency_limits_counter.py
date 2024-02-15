import json
from collections import defaultdict
from typing import Mapping, Optional, Sequence

from .instance import DagsterInstance
from .snap import JobSnapshot
from .storage.dagster_run import DagsterRun
from .storage.tags import (
    GLOBAL_CONCURRENCY_TAG,
    RUN_OP_CONCURRENCY_KEYS,
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
        RUN_OP_CONCURRENCY_KEYS: json.dumps(concurrency_keys_by_node_name),
    }


class GlobalOpConcurrencyLimitsCounter:
    def __init__(
        self,
        instance: DagsterInstance,
        runs: Sequence[DagsterRun],
        in_progress_runs: Sequence[DagsterRun],
    ):
        self._all_concurrency_keys_by_run = {}
        self._root_concurrency_keys_by_run = {}
        self._concurrency_info_by_key = {}
        self._launched_step_counts_by_key = defaultdict(int)
        self._in_progress_run_steps_by_key = defaultdict(dict)

        # fetch all the concurrency info for all of the runs at once, so we can claim in the correct
        # priority order
        self._fetch_concurrency_info(instance, runs)

        # fetch all the outstanding concurrency keys for in-progress runs
        self._process_in_progress_runs(in_progress_runs)

    def _root_concurrency_keys_for_run(self, run: DagsterRun) -> Sequence[Optional[str]]:
        if run.run_id in self._root_concurrency_keys_by_run:
            return self._root_concurrency_keys_by_run[run.run_id]

        root_concurrency_keys_str = run.tags.get(RUN_OP_ROOT_CONCURRENCY_KEYS)
        if not root_concurrency_keys_str:
            self._root_concurrency_keys_by_run[run.run_id] = []
            return []
        keys = json.loads(root_concurrency_keys_str)
        self._root_concurrency_keys_by_run[run.run_id] = keys
        return keys

    def _concurrency_keys_for_run_by_step(self, run: DagsterRun) -> Mapping[str, Optional[str]]:
        if run.run_id in self._all_concurrency_keys_by_run:
            return self._all_concurrency_keys_by_run[run.run_id]

        all_concurrency_keys_str = run.tags.get(RUN_OP_CONCURRENCY_KEYS)
        if not all_concurrency_keys_str:
            self._all_concurrency_keys_by_run[run.run_id] = {}
            return {}
        keys = json.loads(all_concurrency_keys_str)
        self._all_concurrency_keys_by_run[run.run_id] = keys
        return keys

    def _fetch_concurrency_info(self, instance: DagsterInstance, runs: Sequence[DagsterRun]):
        all_concurrency_keys = set()
        for run in runs:
            root_concurrency_keys = self._root_concurrency_keys_for_run(run)
            all_concurrency_keys.update([key for key in root_concurrency_keys if key])

        for key in all_concurrency_keys:
            self._concurrency_info_by_key[key] = instance.event_log_storage.get_concurrency_info(
                key
            )

    def _process_in_progress_runs(self, in_progress_runs):
        for run in in_progress_runs:
            keys_by_step = self._concurrency_keys_for_run_by_step(run)
            for step_key, concurrency_key in keys_by_step.items():
                if run.run_id not in self._in_progress_run_steps_by_key[concurrency_key]:
                    self._in_progress_run_steps_by_key[concurrency_key][run.run_id] = set(
                        [step_key]
                    )
                else:
                    self._in_progress_run_steps_by_key[concurrency_key][run.run_id].add(step_key)

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        root_concurrency_keys = self._root_concurrency_keys_by_run.get(run.run_id)
        if not root_concurrency_keys or any(
            [not isinstance(key, str) for key in root_concurrency_keys]
        ):
            return False

        for concurrency_key in root_concurrency_keys:
            if concurrency_key not in self._concurrency_info_by_key:
                return False

            key_info = self._concurrency_info_by_key[concurrency_key]
            headroom = (
                key_info.slot_count
                - len(key_info.pending_steps)
                - self._launched_step_counts_by_key[concurrency_key]
            )
            if headroom <= 0:
                continue

            # if there is headroom, check the in-progress runs, and the launched runs
            if headroom > self._get_in_progress_outstanding_step_counts_for_key(concurrency_key):
                return False

        return True

    def _get_in_progress_outstanding_step_counts_for_key(self, concurrency_key: str) -> int:
        run_step_keys = self._in_progress_run_steps_by_key[concurrency_key]
        assert concurrency_key in self._concurrency_info_by_key
        key_info = self._concurrency_info_by_key[concurrency_key]
        for pending_step in key_info.pending_steps:
            if pending_step.run_id in run_step_keys:
                # if the run/step is already in the pending steps, it's already been accounted for
                run_step_keys[pending_step.run_id].remove(pending_step.step_key)

        # TODO: this is overcounting the outstanding steps, because we're also including counts of
        # steps for in-progress runs that have already completed. To adjust for this, we would need
        # to fetch the step-stats for every in-progress run (potentially very expensive) and
        # subtract the step keys that have completed.

        count = 0
        for step_keys in run_step_keys.values():
            count += len(step_keys)

        return count

    def update_counters_with_launched_item(self, run: DagsterRun):
        for concurrency_key in self._concurrency_keys_for_run_by_step(run).values():
            if concurrency_key:
                self._launched_step_counts_by_key[concurrency_key] += 1
