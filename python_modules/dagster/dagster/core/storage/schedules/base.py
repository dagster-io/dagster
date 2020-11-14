import abc

import six


class ScheduleStorage(six.with_metaclass(abc.ABCMeta)):
    """Abstract class for managing persistance of scheduler artifacts
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
    def get_job_tick_stats(self, job_origin_id):
        """Get tick stats for a given job.

        Args:
            job_origin_id (str): The id of the ExternalJob target
        """

    @abc.abstractmethod
    def upgrade(self):
        """Perform any needed migrations
        """

    def optimize_for_dagit(self, statement_timeout):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""
