import six
import abc

from collections import namedtuple
from dagster import check


class Scheduler(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def create_schedule(self, *args, **kwargs):
        '''Create a new pipeline schedule.

        Passes args and kwargs to the new Schedule.

        Returns:
            PipelineSchedule
        '''

    @abc.abstractmethod
    def remove_schedule(self, id_):
        '''Deletes a pipeline schedule.

        Args:
            id_ (str): The id of the schedule
        '''

    @abc.abstractmethod
    def all_schedules(self):
        '''Return all the schedules present in the storage.

        Returns:
            Iterable[(str, PipelineSchedule)]: Tuples of schedule_id, schedule.
        '''

    @abc.abstractmethod
    def all_schedules_for_pipeline(self, pipeline_name):
        '''Return all the schedules present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            Iterable[(str, PipelineSchedule)]: Tuples of schedule_id, schedule.
        '''

    @abc.abstractmethod
    def get_schedule_by_id(self, id_):
        '''Get a schedule by its id.

        Args:
            id_ (str): The id of the schedule

        Returns:
            Optional[PipelineSchedule]
        '''

    @abc.abstractmethod
    def start_schedule(self, id_, python_path, repository_path):
        '''Start a pipeline schedule.

        Args:
            id_ (str): The id of the schedule
            python_path (str): Path to the virtualenv python executable
            repository_path (str): Path to the repository yaml file for the repository the schedule
                targets
        '''

    @abc.abstractmethod
    def end_schedule(self, id_):
        '''Ends an existing pipeline schedule

        Args:
            id_ (str): The id of the schedule
        '''


class RunSchedule(
    namedtuple(
        'RunSchedule', 'schedule_id name cron_schedule execution_params python_path repository_path'
    )
):
    def __new__(cls, schedule_id, name, cron_schedule, execution_params, **kwargs):
        return super(RunSchedule, cls).__new__(
            cls,
            check.str_param(schedule_id, 'schedule_id'),
            check.str_param(name, 'name'),
            check.str_param(cron_schedule, 'cron_schedule'),
            check.dict_param(execution_params, 'execution_params'),
            check.opt_str_param(kwargs.get("python_path"), 'python_path'),
            check.opt_str_param(kwargs.get("repository_path"), 'repository_path'),
        )

    def start_schedule(self, python_path, repository_path):
        return RunSchedule(
            self.schedule_id,
            self.name,
            self.cron_schedule,
            self.execution_params,
            python_path=python_path,
            repository_path=repository_path,
        )

    def end_schedule(self):
        return RunSchedule(self.schedule_id, self.name, self.cron_schedule, self.execution_params)
