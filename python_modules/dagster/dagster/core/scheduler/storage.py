import abc
import io
import os
import shutil
import warnings
from collections import OrderedDict

import six

from dagster import check, utils
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple

from .scheduler import Schedule, ScheduleStatus


class ScheduleStorage(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def all_schedules(self, status):
        '''Return all schedules present in the storage
        '''

    @abc.abstractmethod
    def get_schedule_by_name(self, schedule_name):
        '''Return the unique schedule with the given name
        '''

    @abc.abstractmethod
    def add_schedule(self, schedule):
        '''Add a schedule to storage.

        Args:
            schedule (Schedule): The schedule to add
        '''

    @abc.abstractmethod
    def update_schedule(self, schedule):
        '''Update a schedule already in storage, using schedule_id to match schedules.

        Args:
            schedule (Schedule): The schedule to add
        '''

    @abc.abstractmethod
    def delete_schedule(self, schedule):
        '''Delete a schedule from storage.

        Args:
            schedule (Schedule): The schedule to delete
        '''

    @abc.abstractmethod
    def wipe(self):
        '''Delete all schedules from storage
        '''

    @abc.abstractmethod
    def get_log_path(self, schedule):
        '''Get path to store logs for schedule
        '''


class FilesystemScheduleStorage(ScheduleStorage):
    def __init__(self, base_dir, repository_name=None):
        self._base_dir = check.str_param(base_dir, 'base_dir')
        self._schedules = OrderedDict()
        self._repository_name = repository_name
        self._load_schedules()

    def all_schedules(self, status=None):
        status = check.opt_inst_param(status, 'status', ScheduleStatus)

        if status:
            return [s for s in self._schedules.values() if s.status == status]

        return [s for s in self._schedules.values()]

    def get_schedule_by_name(self, schedule_name):
        return self._schedules.get(schedule_name)

    def add_schedule(self, schedule):
        check.inst_param(schedule, 'schedule', Schedule)
        self._schedules[schedule.name] = schedule
        self._write_schedule_to_file(schedule)

    def update_schedule(self, schedule):
        check.inst_param(schedule, 'schedule', Schedule)
        if schedule.name not in self._schedules:
            raise DagsterInvariantViolationError(
                'Schedule {name} is not present in storage'.format(name=schedule.name)
            )

        self.add_schedule(schedule)

    def delete_schedule(self, schedule):
        check.inst_param(schedule, 'schedule', Schedule)
        self._schedules.pop(schedule.name)
        self._delete_schedule_file(schedule)

    def wipe(self):
        shutil.rmtree(self._base_dir)

    def get_log_path(self, schedule):
        check.inst_param(schedule, 'schedule', Schedule)
        return os.path.join(
            self._base_dir,
            self._repository_name,
            'logs',
            '{}_{}'.format(schedule.name, schedule.schedule_id),
        )

    def _write_schedule_to_file(self, schedule):
        metadata_file = os.path.join(
            self._base_dir,
            self._repository_name,
            '{}_{}.json'.format(schedule.name, schedule.schedule_id),
        )
        with io.open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(six.text_type(serialize_dagster_namedtuple(schedule)))

        return metadata_file

    def _delete_schedule_file(self, schedule):
        metadata_file = os.path.join(
            self._base_dir,
            self._repository_name,
            '{}_{}.json'.format(schedule.name, schedule.schedule_id),
        )

        os.remove(metadata_file)

    def _load_schedules(self):
        schedules_dir = os.path.join(self._base_dir, self._repository_name)
        utils.mkdir_p(schedules_dir)

        for file in os.listdir(schedules_dir):
            if not file.endswith('.json'):
                continue
            file_path = os.path.join(schedules_dir, file)
            with open(file_path) as data:
                try:
                    schedule = deserialize_json_to_dagster_namedtuple(data.read())
                    self._schedules[schedule.name] = schedule

                except Exception as ex:  # pylint: disable=broad-except
                    warnings.warn(
                        'Could not parse dagster schedule from {file_name} in {dir_name}. '
                        '{ex}: {msg}'.format(
                            file_name=file, dir_name=self._base_dir, ex=type(ex).__name__, msg=ex
                        )
                    )
                    continue
