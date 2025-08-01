import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class RunInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for run operations."""

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    # Storage access
    @property
    def run_storage(self):
        return self._instance.run_storage

    @property
    def event_log_storage(self):
        return self._instance.event_log_storage

    # Event reporting
    def report_engine_event(self, message, dagster_run, event_data):
        return self._instance.report_engine_event(message, dagster_run, event_data)

    def report_dagster_event(self, event, run_id, log_level=logging.INFO):
        return self._instance.report_dagster_event(event, run_id, log_level)

    def report_run_failed(self, dagster_run):
        return self._instance.report_run_failed(dagster_run)

    # Run operations
    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)

    def get_backfill(self, backfill_id):
        return self._instance.get_backfill(backfill_id)

    def all_logs(self, run_id, of_type=None):
        return self._instance.all_logs(run_id, of_type)

    def has_run(self, run_id):
        return self._instance.has_run(run_id)

    def get_execution_plan_snapshot(self, snapshot_id):
        return self._instance.get_execution_plan_snapshot(snapshot_id)

    # DynamicPartitionsStore access
    def as_dynamic_partitions_store(self):
        return self._instance  # Instance implements DynamicPartitionsStore
