from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class AssetInstanceOps:
    """Simple wrapper to provide clean access to DagsterInstance for asset operations."""

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    # Storage access
    @property
    def event_log_storage(self):
        return self._instance._event_storage  # noqa: SLF001

    # Event operations
    def get_event_records(self, event_records_filter):
        return self._instance.get_event_records(event_records_filter)

    def get_records_for_run(self, run_id, cursor=None, of_type=None, limit=None, ascending=False):
        return self._instance.get_records_for_run(run_id, cursor, of_type, limit, ascending)

    def report_engine_event(self, message, dagster_run, event_data):
        return self._instance.report_engine_event(message, dagster_run, event_data)

    def report_dagster_event(self, run_id, dagster_event):
        return self._instance.report_dagster_event(dagster_event, run_id)

    # Other dependencies used by asset methods
    def get_run_by_id(self, run_id):
        return self._instance.get_run_by_id(run_id)

    @property
    def can_read_asset_status_cache(self):
        return self._instance.can_read_asset_status_cache

    @property
    def event_storage(self):
        return self._instance._event_storage  # noqa: SLF001
