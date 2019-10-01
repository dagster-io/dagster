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


def get_schedule_change_set(old_schedules, new_schedule_defs):
    check.list_param(old_schedules, 'old_schedules', Schedule)
    check.list_param(new_schedule_defs, 'new_schedule_defs', ScheduleDefinition)

    new_schedules_defs_dict = {s.name: s for s in new_schedule_defs}
    old_schedules_dict = {s.schedule_definition.name: s for s in old_schedules}

    new_schedule_defs_names = set(new_schedules_defs_dict.keys())
    old_schedules_names = set(old_schedules_dict.keys())

    added_schedules = new_schedule_defs_names - old_schedules_names
    changed_schedules = new_schedule_defs_names & old_schedules_names
    removed_schedules = old_schedules_names - new_schedule_defs_names

    changeset = []

    for schedule_name in added_schedules:
        changeset.append(("add", schedule_name, []))

    for schedule_name in changed_schedules:
        changes = []

        old_schedule_def = old_schedules_dict[schedule_name].schedule_definition
        new_schedule_def = new_schedules_defs_dict[schedule_name]

        if old_schedule_def.cron_schedule != new_schedule_def.cron_schedule:
            changes.append(
                ("cron_schedule", (old_schedule_def.cron_schedule, new_schedule_def.cron_schedule))
            )

        if old_schedule_def.execution_params != new_schedule_def.execution_params:
            changes.append(("execution_params", '[modified]'))

        if len(changes) > 0:
            changeset.append(("change", schedule_name, changes))

    for schedule_name in removed_schedules:
        changeset.append(("remove", schedule_name, []))

    return changeset


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

    def up(self, python_path, repository_path):
        '''SchedulerHandle stores a list of up-to-date ScheduleDefinitions and a reference to a
        ScheduleStorage. When `up` is called, it reconciles the ScheduleDefinitions list and
        ScheduleStorage to ensure there is a 1-1 correlation between ScheduleDefinitions and
        Schedules, where the ScheduleDefinitions list is the source of truth.

        If a new ScheduleDefinition is introduced, a new Schedule is added to storage with status
        ScheduleStatus.STOPPED.

        For every previously existing ScheduleDefinition (where schedule_name is the primary key),
        any changes to the definition are persisted in the corresponding Schedule and the status is
        left unchanged.

        For every ScheduleDefinitions that is removed, the corresponding Schedule is removed from
        the storage.
        '''

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

    def get_change_set(self):
        schedule_defs = self.all_schedule_defs()
        schedules = self._schedule_storage.all_schedules()
        return get_schedule_change_set(schedules, schedule_defs)

    def all_schedule_defs(self):
        return self._schedule_defs

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
            name (str): The name of the schedule

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
            schedule_name (string): The schedule to end and delete
        '''

    @abc.abstractmethod
    def log_path_for_schedule(self, schedule_name):
        '''Get the path to the log file for the given schedule

        Args:
            schedule_name (string): The schedule to get the log file for
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
