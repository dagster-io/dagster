import abc

import six


class ScheduleStorage(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def all_schedules(self, repository=None):
        '''Return all schedules present in the storage
        '''

    @abc.abstractmethod
    def get_schedule_by_name(self, repository, schedule_name):
        '''Return the unique schedule with the given name
        '''

    @abc.abstractmethod
    def add_schedule(self, repository, schedule):
        '''Add a schedule to storage.

        Args:
            schedule (Schedule): The schedule to add
        '''

    @abc.abstractmethod
    def update_schedule(self, repository, schedule):
        '''Update a schedule already in storage, using schedule name to match schedules.

        Args:
            schedule (Schedule): The schedule to add
        '''

    @abc.abstractmethod
    def delete_schedule(self, repository, schedule):
        '''Delete a schedule from storage.

        Args:
            schedule (Schedule): The schedule to delete
        '''

    @abc.abstractmethod
    def wipe(self):
        '''Delete all schedules from storage
        '''
