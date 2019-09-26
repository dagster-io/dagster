import abc
import uuid
from collections import namedtuple
from enum import Enum

import six

from dagster import check
from dagster.core.definitions.schedule import ScheduleDefinition
from dagster.core.serdes import whitelist_for_serdes


@whitelist_for_serdes
class ScheduleStatus(Enum):
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ENDED = 'ENDED'


class SchedulerHandle(object):
    def __init__(self, scheduler_type, schedule_defs, artifacts_dir, repository_name):
        from .storage import FilesystemScheduleStorage

        check.subclass_param(scheduler_type, 'scheduler_type', Scheduler)
        check.list_param(schedule_defs, 'schedule_defs', ScheduleDefinition)
        check.str_param(artifacts_dir, 'artifacts_dir')
        check.str_param(repository_name, 'repository_name')

        self._Scheduler = scheduler_type
        self._artifacts_dir = artifacts_dir
        self._schedule_defs = schedule_defs

        self._schedule_storage = FilesystemScheduleStorage(
            artifacts_dir, repository_name=repository_name
        )

    def init(self, python_path, repository_path):
        for schedule_def in self._schedule_defs:
            # If a schedule already exists for schedule_def, overwrite bash script and
            # metadata file
            existing_schedule = self._schedule_storage.get_schedule_by_name(schedule_def.name)
            if existing_schedule:
                # Use the old schedule's ID and status, but replace schedule_def,
                # python_path, and repository_path
                schedule = Schedule(
                    existing_schedule.schedule_id,
                    schedule_def,
                    existing_schedule.status,
                    python_path,
                    repository_path,
                )

                self._schedule_storage.update_schedule(schedule)
            else:
                schedule_id = str(uuid.uuid4())
                schedule = Schedule(
                    schedule_id, schedule_def, ScheduleStatus.STOPPED, python_path, repository_path
                )

                self._schedule_storage.add_schedule(schedule)

        # Delete all existing schedules that are not in schedule_defs
        schedule_def_names = {s.name for s in self._schedule_defs}
        existing_schedule_names = set(
            [s.schedule_definition.name for s in self._schedule_storage.all_schedules()]
        )
        schedule_names_to_delete = existing_schedule_names - schedule_def_names

        TempScheduler = self._Scheduler(self._artifacts_dir, self._schedule_storage)
        for schedule_name in schedule_names_to_delete:
            TempScheduler.end_schedule(schedule_name)

    def get_scheduler(self):
        return self._Scheduler(self._artifacts_dir, self._schedule_storage)


class Scheduler(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def all_schedules(self, status):
        '''Return all the schedules present in the storage.

        Returns:
            Iterable[RunningSchedule]: List of running scheudles.
        '''

    @abc.abstractmethod
    def get_schedule_by_name(self, name):
        '''Get a schedule by its name.

        Args:
            name (str): The id of the schedule

        Returns:
            Optional[RunningSchedule]
        '''

    @abc.abstractmethod
    def start_schedule(self, schedule_name):
        '''Resume a pipeline schedule.

        Args:
            schedule_name (string): The schedule to resume
        '''

    @abc.abstractmethod
    def stop_schedule(self, schedule_name):
        '''Stops an existing pipeline schedule

        Args:
            schedule_name (string): The schedule to stop
        '''

    @abc.abstractmethod
    def end_schedule(self, schedule_name):
        '''Resume a pipeline schedule.

        Args:
            schedule_name (string): The schedule to resume
        '''


@whitelist_for_serdes
class Schedule(
    namedtuple('Schedule', 'schedule_id schedule_definition status python_path repository_path')
):
    def __new__(
        cls, schedule_id, schedule_definition, status, python_path=None, repository_path=None
    ):
        return super(Schedule, cls).__new__(
            cls,
            check.str_param(schedule_id, 'schedule_id'),
            check.inst_param(schedule_definition, 'schedule_definition', ScheduleDefinition),
            check.inst_param(status, 'status', ScheduleStatus),
            check.opt_str_param(python_path, 'python_path'),
            check.opt_str_param(repository_path, 'repository_path'),
        )

    def with_status(self, status):
        check.inst_param(status, 'status', ScheduleStatus)

        return Schedule(
            self.schedule_id,
            self.schedule_definition,
            status=status,
            python_path=self.python_path,
            repository_path=self.repository_path,
        )
