import os
from typing import Optional

import yaml

from dagster import _check as check
from dagster._config import StringSource
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import mkdir_p

from .base_storage import DagsterStorage
from .event_log.base import EventLogStorage
from .event_log.sqlite.sqlite_event_log import SqliteEventLogStorage
from .runs.base import RunStorage
from .runs.sqlite.sqlite_run_storage import SqliteRunStorage
from .schedules.base import ScheduleStorage
from .schedules.sqlite.sqlite_schedule_storage import SqliteScheduleStorage


def _runs_directory(base):
    return os.path.join(base, "history", "")


def _event_logs_directory(base):
    return os.path.join(base, "history", "runs", "")


def _schedule_directory(base):
    return os.path.join(base, "schedules")


class DagsterSqliteStorage(DagsterStorage, ConfigurableClass):
    """SQLite-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    This is the default run storage when none is specified in the ``dagster.yaml``.

    To explicitly specify SQLite for run storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. code-block:: YAML

        storage:
          sqlite:
            base_dir: /path/to/dir

    """

    def __init__(self, base_dir, inst_data=None):
        self.base_dir = check.str_param(base_dir, "base_dir")
        self._run_storage = SqliteRunStorage.from_local(_runs_directory(base_dir))
        self._event_log_storage = SqliteEventLogStorage(_event_logs_directory(base_dir))
        self._schedule_storage = SqliteScheduleStorage.from_local(_schedule_directory(base_dir))
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": StringSource}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return DagsterSqliteStorage.from_local(inst_data=inst_data, **config_value)

    @classmethod
    def from_local(cls, base_dir, inst_data=None):
        check.str_param(base_dir, "base_dir")
        mkdir_p(base_dir)
        return cls(base_dir, inst_data=inst_data)

    @property
    def event_log_storage(self) -> EventLogStorage:
        return self._event_log_storage

    @property
    def run_storage(self) -> RunStorage:
        return self._run_storage

    @property
    def schedule_storage(self) -> ScheduleStorage:
        return self._schedule_storage

    @property
    def event_storage_data(self) -> Optional[ConfigurableClassData]:
        return ConfigurableClassData(
            "dagster._core.storage.event_log",
            "SqliteEventLogStorage",
            yaml.dump({"base_dir": _runs_directory(self.base_dir)}, default_flow_style=False),
        )

    @property
    def run_storage_data(self) -> Optional[ConfigurableClassData]:
        return ConfigurableClassData(
            "dagster._core.storage.runs",
            "SqliteRunStorage",
            yaml.dump({"base_dir": _event_logs_directory(self.base_dir)}, default_flow_style=False),
        )

    @property
    def schedule_storage_data(self) -> Optional[ConfigurableClassData]:
        return ConfigurableClassData(
            "dagster._core.storage.schedules",
            "SqliteScheduleStorage",
            yaml.dump({"base_dir": _schedule_directory(self.base_dir)}, default_flow_style=False),
        )
