from abc import ABC, abstractmethod

from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance

from .event_log.base import EventLogStorage
from .runs.base import RunStorage
from .schedules.base import ScheduleStorage


class DagsterStorage(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Abstract base class for Dagster persistent storage, for reading and writing data for runs,
    events, and schedule/sensor state.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagster-webserver`` and ``dagster-daemon`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @property
    @abstractmethod
    def event_log_storage(self) -> EventLogStorage[T_DagsterInstance]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def run_storage(self) -> RunStorage[T_DagsterInstance]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def schedule_storage(self) -> ScheduleStorage[T_DagsterInstance]:
        raise NotImplementedError()
