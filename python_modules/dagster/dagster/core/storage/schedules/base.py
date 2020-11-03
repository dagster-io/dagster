import abc

import six


class ScheduleStorage(six.with_metaclass(abc.ABCMeta)):
    """Abstract class for managing persistance of scheduler artifacts
    """

    @abc.abstractmethod
    def all_stored_schedule_state(self, repository_origin_id=None):
        """Return all ScheduleStates present in storage

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
        """

    @abc.abstractmethod
    def get_schedule_state(self, schedule_origin_id):
        """Return the unique schedule with the given id

        Args:
            schedule_origin_id (str): The unique schedule identifier
        """

    @abc.abstractmethod
    def add_schedule_state(self, schedule):
        """Add a schedule to storage.

        Args:
            schedule (ScheduleState): The schedule to add
        """

    @abc.abstractmethod
    def update_schedule_state(self, schedule):
        """Update a schedule already in storage, using schedule name to match schedules.

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule (ScheduleState): The schedule to update
        """

    @abc.abstractmethod
    def delete_schedule_state(self, schedule_origin_id):
        """Delete a schedule from storage.

        Args:
            schedule_origin_id (str): The id of the ExternalSchedule target to delete
        """

    @abc.abstractmethod
    def get_schedule_ticks(self, schedule_origin_id):
        """Get all schedule ticks for a given schedule.

        Args:
            schedule_origin_id (str): The id of the ExternalSchedule target
        """

    @abc.abstractmethod
    def get_latest_tick(self, schedule_origin_id):
        """Get the most recent tick that ran for a given schedule.

        Args:
            schedule_origin_id (str): The id of the ExternalSchedule target
        """

    @abc.abstractmethod
    def get_schedule_tick_stats(self, schedule_origin_id):
        """Get summary statistics for schedule ticks for a given schedule

        Args:
            schedule_origin_id (str): The id of the ExternalSchedule target
        """

    @abc.abstractmethod
    def create_schedule_tick(self, schedule_tick_data):
        """Add a schedule tick to storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            schedule_tick_data (ScheduleTickData): The schedule tick to add
        """

    @abc.abstractmethod
    def update_schedule_tick(self, tick):
        """Update a schedule tick already in storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            tick (ScheduleTick): The schedule tick to update
        """

    @abc.abstractmethod
    def wipe(self):
        """Delete all schedules from storage
        """

    @abc.abstractmethod
    def all_stored_job_state(self, repository_origin_id=None, job_type=None):
        """Return all JobStates present in storage

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
            job_type (Optional[JobType]): The JobType to scope results to
        """

    @abc.abstractmethod
    def get_job_state(self, job_origin_id):
        """Return the unique job with the given id

        Args:
            job_origin_id (str): The unique job identifier
        """

    @abc.abstractmethod
    def add_job_state(self, job):
        """Add a job to storage.

        Args:
            job (JobState): The job to add
        """

    @abc.abstractmethod
    def update_job_state(self, job):
        """Update a job in storage.

        Args:
            job (JobState): The job to update
        """

    @abc.abstractmethod
    def delete_job_state(self, job_origin_id):
        """Delete a job in storage.

        Args:
            job_origin_id (str): The id of the ExternalJob target to delete
        """

    @abc.abstractmethod
    def get_job_ticks(self, job_origin_id):
        """Get the ticks for a given job.

        Args:
            job_origin_id (str): The id of the ExternalJob target
        """

    @abc.abstractmethod
    def has_job_tick(self, job_origin_id, execution_key, statuses=None):
        """Checks if there is a job tick for a given job / execution_key in storage.

        Args:
            job_origin_id (str): The id of the ExternalJob target
            execution_key (str): User-provided key that identifies a given job execution
            statuses (Optional[List[JobTickStatus]]): List of statuses to filter ticks by
        """

    @abc.abstractmethod
    def get_latest_job_tick(self, job_origin_id):
        """Get the most recent tick for a given job.

        Args:
            job_origin_id (str): The id of the ExternalJob target
        """

    @abc.abstractmethod
    def create_job_tick(self, job_tick_data):
        """Add a job tick to storage.

        Args:
            repository_name (str): The repository the schedule belongs to
            job_tick_data (JobTickData): The job tick to add
        """

    @abc.abstractmethod
    def update_job_tick(self, tick):
        """Update a job tick already in storage.

        Args:
            tick (ScheduleTick): The job tick to update
        """

    @abc.abstractmethod
    def upgrade(self):
        """Perform any needed migrations
        """

    def optimize_for_dagit(self, statement_timeout):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""
