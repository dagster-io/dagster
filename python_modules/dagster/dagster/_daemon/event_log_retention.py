import datetime
import os

from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.daemon import IntervalDaemon
from dagster._time import get_current_datetime

_INTERVAL_SECONDS = int(os.environ.get("EVENT_LOG_RETENTION_DAEMON_INTERVAL_SECONDS", "3600"))


class EventLogRetentionDaemon(IntervalDaemon):
    def __init__(self, interval_seconds: int = _INTERVAL_SECONDS):
        super().__init__(interval_seconds=interval_seconds)

    @classmethod
    def daemon_type(cls):
        return "EVENT_LOG_RETENTION"

    def run_iteration(self, workspace_process_context: IWorkspaceProcessContext):
        yield
        instance = workspace_process_context.instance
        days = instance.event_log_retention_days
        if days is None:
            return
        cutoff = (get_current_datetime() - datetime.timedelta(days=days)).timestamp()
        deleted = instance.event_log_storage.purge_events(cutoff)
        self._logger.info(
            f"Purged {deleted} non-asset event log row(s) older than {days} day(s).",
        )
