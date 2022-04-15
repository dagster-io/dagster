from abc import ABC, abstractproperty
from typing import Optional

from dagster.core.instance import MayHaveInstanceWeakref
from dagster.serdes import ConfigurableClassData

from .event_log.base import EventLogStorage
from .runs.base import RunStorage
from .schedules.base import ScheduleStorage


class DagsterStorage(ABC, MayHaveInstanceWeakref):
    """Abstract base class for storing pipeline run history.

    Note that run storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.runs.SqlRunStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractproperty
    def event_log_storage(self) -> EventLogStorage:
        raise NotImplementedError()

    @abstractproperty
    def run_storage(self) -> RunStorage:
        raise NotImplementedError()

    @abstractproperty
    def schedule_storage(self) -> ScheduleStorage:
        raise NotImplementedError()

    @abstractproperty
    def event_storage_data(self) -> Optional[ConfigurableClassData]:
        raise NotImplementedError()

    @abstractproperty
    def run_storage_data(self) -> Optional[ConfigurableClassData]:
        raise NotImplementedError()

    @abstractproperty
    def schedule_storage_data(self) -> Optional[ConfigurableClassData]:
        raise NotImplementedError()
