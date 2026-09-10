import datetime
import os

from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.daemon import IntervalDaemon
from dagster._time import get_current_datetime

_INTERVAL_SECONDS = int(os.environ.get("EVENT_LOG_RETENTION_DAEMON_INTERVAL_SECONDS", "3600"))


class EventLogRetentionDaemon(IntervalDaemon):
    def __init__(self, interval_seconds: int = _INTERVAL_SECONDS):
        super().__init__(interval_seconds=interval_seconds)
        self._warned_run_sharded = False

    @classmethod
    def daemon_type(cls):
        return "EVENT_LOG_RETENTION"

    def run_iteration(self, workspace_process_context: IWorkspaceProcessContext):
        yield
        instance = workspace_process_context.instance
        days = instance.event_log_retention_days
        if days is None:
            return
        event_log_storage = instance.event_log_storage
        # per-run sqlite stores most rows in per-run shard files that the index connection
        # never sees - purge only touches the index shard. warn once so operators understand.
        if event_log_storage.is_run_sharded and not self._warned_run_sharded:
            self._logger.warning(
                "Event log retention is running against a run-sharded storage (default sqlite). "
                "Only rows on the shared index shard will be purged; per-run shard files are "
                "untouched. Use a consolidated storage (postgres, mysql, or consolidated sqlite) "
                "for full retention.",
            )
            self._warned_run_sharded = True
        cutoff = (get_current_datetime() - datetime.timedelta(days=days)).timestamp()
        deleted = event_log_storage.purge_events(cutoff)
        if deleted:
            self._logger.info(
                f"Purged {deleted} non-asset event log row(s) older than {days} day(s).",
            )
        else:
            self._logger.debug(
                f"No non-asset event log rows older than {days} day(s) to purge.",
            )
