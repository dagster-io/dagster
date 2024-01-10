from typing import Sequence

from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun


class GlobalOpConcurrencyLimitsCounter:
    def __init__(self, instance: DagsterInstance, runs: Sequence[DagsterRun]):
        self._snapshots_by_id = {}
        self._concurrency_keys_by_run = {}
        self._concurrency_info_by_key = {}

        # fetch all the concurrency info for all of the runs at once, so we can claim in the correct
        # priority order
        self._initialize_concurrency_keys(instance, runs)
        self._fetch_concurrency_info(instance)

    def _initialize_concurrency_keys(self, instance: DagsterInstance, runs: Sequence[DagsterRun]):
        for run in runs:
            if not run.job_snapshot_id or not run.asset_selection:
                continue

            if run.job_snapshot_id in self._snapshots_by_id:
                snapshot = self._snapshots_by_id[run.job_snapshot_id]
            else:
                snapshot = instance.get_job_snapshot(run.job_snapshot_id)
                self._snapshots_by_id[run.job_snapshot_id] = snapshot

            self._concurrency_keys_by_run[run.run_id] = [
                op_snap.tags.get("dagster/concurrency_key")
                for op_snap in snapshot.node_defs_snapshot.op_def_snaps
            ]

    def _fetch_concurrency_info(self, instance: DagsterInstance):
        all_concurrency_keys = set()
        for keys in self._concurrency_keys_by_run.values():
            all_concurrency_keys.update([key for key in keys if key])

        for key in all_concurrency_keys:
            self._concurrency_info_by_key[key] = instance.event_log_storage.get_concurrency_info(
                key
            )

    def is_blocked(self, run: DagsterRun) -> bool:
        # if any of the ops in the run can make progress (not blocked by concurrency keys), we
        # should dequeue
        concurrency_keys = self._concurrency_keys_by_run.get(run.run_id)
        if not concurrency_keys or any([not isinstance(key, str) for key in concurrency_keys]):
            return False

        for concurrency_key in concurrency_keys:
            key_info = self._concurrency_info_by_key[concurrency_key]
            if not key_info or len(key_info.pending_steps) < key_info.slot_count:
                return False

        return True

    def concurrency_keys(self, run: DagsterRun) -> Sequence[str]:
        return [
            key for key in self._concurrency_keys_by_run.get(run.run_id, []) if isinstance(key, str)
        ]
