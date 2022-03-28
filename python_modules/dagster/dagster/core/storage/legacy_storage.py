from dagster import check

from .base_storage import DagsterStorage
from .event_log.base import EventLogStorage
from .runs.base import RunStorage
from .schedules.base import ScheduleStorage


class LegacyStorage(DagsterStorage):
    def __init__(self, run_storage, event_log_storage, schedule_storage):
        self._run_storage = check.inst_param(run_storage, "run_storage", RunStorage)
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", EventLogStorage
        )
        self._schedule_storage = check.inst_param(
            schedule_storage, "schedule_storage", ScheduleStorage
        )
        super().__init__()

    @property
    def event_log_storage(self) -> EventLogStorage:
        return self._event_log_storage

    @property
    def run_storage(self) -> RunStorage:
        return self._run_storage

    @property
    def schedule_storage(self) -> ScheduleStorage:
        return self._schedule_storage
