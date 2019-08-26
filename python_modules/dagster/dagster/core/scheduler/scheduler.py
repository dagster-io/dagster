import abc
from collections import namedtuple

import six

from dagster import check
from dagster.core.definitions.schedule import ScheduleDefinition


class Scheduler(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def all_schedules(self):
        '''Return all the schedules present in the storage.

        Returns:
            Iterable[RunningSchedule]: List of running scheudles.
        '''

    @abc.abstractmethod
    def all_schedules_for_pipeline(self, pipeline_name):
        '''Return all the schedules present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            Iterable[RunningSchedule]: List of running schedules.
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
    def start_schedule(self, schedule_definition, python_path, repository_path):
        '''Start a pipeline schedule.

        Args:
            schedule_definition (ScheduleDefinition): The ScheduleDefintion to start a schedule for
            python_path (str): Path to the virtualenv python executable
            repository_path (str): Path to the repository yaml file for the repository the schedule
                targets
        '''

    @abc.abstractmethod
    def end_schedule(self, schedule_definition):
        '''Ends an existing pipeline schedule

        Args:
            schedule_definition (ScheduleDefinition): The ScheduleDefintion to end a schedule for
        '''


class RunningSchedule(
    namedtuple('RunningSchedule', 'schedule_id schedule_definition python_path repository_path')
):
    def __new__(cls, schedule_id, schedule_definition, python_path=None, repository_path=None):
        return super(RunningSchedule, cls).__new__(
            cls,
            check.str_param(schedule_id, 'schedule_id'),
            check.inst_param(schedule_definition, 'schedule_definition', ScheduleDefinition),
            check.opt_str_param(python_path, 'python_path'),
            check.opt_str_param(repository_path, 'repository_path'),
        )

    def start_schedule(self, python_path, repository_path):
        return RunningSchedule(
            self.schedule_id, self.schedule_definition, python_path, repository_path
        )

    def end_schedule(self):
        return RunningSchedule(
            self.schedule_id, self.schedule_definition, python_path=None, repository_path=None
        )
