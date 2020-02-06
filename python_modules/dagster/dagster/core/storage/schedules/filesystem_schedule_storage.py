import io
import os
import shutil
import warnings
from collections import OrderedDict

import six

from dagster import check, utils
from dagster.core.definitions import RepositoryDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.scheduler import Schedule
from dagster.core.serdes import (
    ConfigurableClass,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)

from .base import ScheduleStorage


class FilesystemScheduleStorage(ScheduleStorage, ConfigurableClass):
    def __init__(self, base_dir, inst_data=None):
        self._base_dir = check.str_param(base_dir, 'base_dir')
        self._inst_data = inst_data
        self._schedules = OrderedDict()
        self._load_schedules()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {'base_dir': str}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return FilesystemScheduleStorage.from_local(inst_data=inst_data, **config_value)

    @staticmethod
    def from_local(base_dir, inst_data=None):
        return FilesystemScheduleStorage(base_dir, inst_data)

    def all_schedules(self, repository=None):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        # TODO: Check for repository=None

        if repository.name not in self._schedules:
            return []

        return [s for s in self._schedules[repository.name].values()]

    def get_schedule_by_name(self, repository, schedule_name):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')

        if repository.name not in self._schedules:
            return None

        return self._schedules[repository.name].get(schedule_name)

    def add_schedule(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        if not repository.name in self._schedules:
            self._schedules[repository.name] = OrderedDict()

        self._schedules[repository.name][schedule.name] = schedule
        self._write_schedule_to_file(repository, schedule)

    def update_schedule(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        if repository.name not in self._schedules:
            raise DagsterInvariantViolationError(
                'Repository {repository_name} is not present in storage'.format(
                    repository_name=repository.name
                )
            )

        if schedule.name not in self._schedules[repository.name]:
            raise DagsterInvariantViolationError(
                'Schedule {name} is not present in storage'.format(name=schedule.name)
            )

        self.add_schedule(repository, schedule)

    def delete_schedule(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        if repository.name not in self._schedules:
            raise DagsterInvariantViolationError(
                'Repository {repository_name} is not present in storage'.format(
                    repository_name=repository.name
                )
            )

        if schedule.name not in self._schedules[repository.name]:
            raise DagsterInvariantViolationError(
                'Schedule {name} is not present in storage'.format(name=schedule.name)
            )

        self._schedules[repository.name].pop(schedule.name)
        self._delete_schedule_file(repository, schedule)

    def wipe(self):
        self._schedules = OrderedDict()
        for repository_name in self._schedules.keys():
            shutil.rmtree(os.path.join(self._base_dir, repository_name))

    def _write_schedule_to_file(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        repository_folder = os.path.join(self._base_dir, repository.name)
        utils.mkdir_p(repository_folder)

        metadata_file = os.path.join(repository_folder, '{}.json'.format(schedule.name),)

        with io.open(metadata_file, 'w+', encoding='utf-8') as f:
            f.write(six.text_type(serialize_dagster_namedtuple(schedule)))

        return metadata_file

    def _delete_schedule_file(self, repository, schedule):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.inst_param(schedule, 'schedule', Schedule)

        metadata_file = os.path.join(
            self._base_dir, repository.name, '{}.json'.format(schedule.name),
        )

        os.remove(metadata_file)

    def _load_schedules(self):
        schedules_dir = os.path.join(self._base_dir)
        utils.mkdir_p(schedules_dir)

        for repository_name in os.listdir(schedules_dir):
            if not os.path.isdir(os.path.join(schedules_dir, repository_name)):
                continue

            self._schedules[repository_name] = {}
            for file in os.listdir(os.path.join(schedules_dir, repository_name)):
                if not file.endswith('.json'):
                    continue
                file_path = os.path.join(schedules_dir, repository_name, file)
                with open(file_path) as data:
                    try:
                        schedule = deserialize_json_to_dagster_namedtuple(data.read())
                        self._schedules[repository_name][schedule.name] = schedule

                    except Exception as ex:  # pylint: disable=broad-except
                        warnings.warn(
                            'Could not parse dagster schedule from {file_name} in {dir_name}. '
                            '{ex}: {msg}'.format(
                                file_name=file,
                                dir_name=self._base_dir,
                                ex=type(ex).__name__,
                                msg=ex,
                            )
                        )
                        continue
