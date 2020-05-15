import abc

import six


class ScheduleStorage(six.with_metaclass(abc.ABCMeta)):
    '''Abstract class for managing persistance of scheduler artifacts
    '''

    @abc.abstractmethod
    def all_schedules(self, repository_name=None):
        '''Return all schedules present in the storage

        Args:
            repository_name (str): The repository the schedule belongs to
        '''

    @abc.abstractmethod
    def get_schedule_by_name(self, repository_name, schedule_name):
        '''Return the unique schedule with the given name

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule_name (str): The name of the schedule
        '''

    @abc.abstractmethod
    def add_schedule(self, repository_name, schedule):
        '''Add a schedule to storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule (Schedule): The schedule to add
        '''

    @abc.abstractmethod
    def update_schedule(self, repository_name, schedule):
        '''Update a schedule already in storage, using schedule name to match schedules.

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule (Schedule): The schedule to update
        '''

    @abc.abstractmethod
    def delete_schedule(self, repository_name, schedule):
        '''Delete a schedule from storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule (Schedule): The schedule to delete
        '''

    @abc.abstractmethod
    def get_schedule_ticks_by_schedule(self, repository_name, schedule_name):
        '''Get all schedule ticks for a given schedule

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule_name (str): The name of the schedule
        '''

    @abc.abstractmethod
    def get_schedule_tick_stats_by_schedule(self, repository_name, schedule_name):
        '''Get summary statistics for schedule ticks for a given schedule

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule_name (str): The name of the schedule
        '''

    @abc.abstractmethod
    def create_schedule_tick(self, repository_name, schedule_tick_data):
        '''Add a schedule tick to storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule_tick_data (ScheduleTickData): The schedule tick to add
        '''

    @abc.abstractmethod
    def update_schedule_tick(self, repository_name, tick):
        '''Update a schedule tick already in storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            tick (ScheduleTick): The schedule tick to update
        '''

    @abc.abstractmethod
    def wipe(self):
        '''Delete all schedules from storage
        '''
