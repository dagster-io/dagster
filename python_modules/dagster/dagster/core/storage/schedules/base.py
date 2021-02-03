import abc
import datetime
from typing import Iterable, Type

from dagster.core.definitions.job import JobType
from dagster.core.errors import DagsterScheduleWipeRequired
from dagster.core.scheduler.job import JobState, JobStatus, JobTick, JobTickData, JobTickStatus


class ScheduleStorage(abc.ABC):
    """Abstract class for managing persistance of scheduler artifacts"""

    @abc.abstractmethod
    def wipe(self):
        """Delete all schedules from storage"""

    @abc.abstractmethod
    def all_stored_job_state(
        self, repository_origin_id: str = None, job_type: JobType = None
    ) -> Iterable[JobState]:
        """Return all JobStates present in storage

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
            job_type (Optional[JobType]): The JobType to scope results to
        """

    @abc.abstractmethod
    def get_job_state(self, job_origin_id: str) -> JobState:
        """Return the unique job with the given id

        Args:
            job_origin_id (str): The unique job identifier
        """

    @abc.abstractmethod
    def add_job_state(self, job: JobState):
        """Add a job to storage.

        Args:
            job (JobState): The job to add
        """

    @abc.abstractmethod
    def update_job_state(self, job: JobState):
        """Update a job in storage.

        Args:
            job (JobState): The job to update
        """

    @abc.abstractmethod
    def delete_job_state(self, job_origin_id: str):
        """Delete a job in storage.

        Args:
            job_origin_id (str): The id of the ExternalJob target to delete
        """

    @abc.abstractmethod
    def get_job_ticks(
        self, job_origin_id: str, before: float = None, after: float = None, limit: int = None
    ) -> Iterable[JobTick]:
        """Get the ticks for a given job.

        Args:
            job_origin_id (str): The id of the ExternalJob target
        """

    @abc.abstractmethod
    def get_latest_job_tick(self, job_origin_id: str) -> JobTick:
        """Get the most recent tick for a given job.

        Args:
            job_origin_id (str): The id of the ExternalJob target
        """

    @abc.abstractmethod
    def create_job_tick(self, job_tick_data: JobTickData):
        """Add a job tick to storage.

        Args:
            job_tick_data (JobTickData): The job tick to add
        """

    @abc.abstractmethod
    def update_job_tick(self, tick: JobTick):
        """Update a job tick already in storage.

        Args:
            tick (JobTick): The job tick to update
        """

    @abc.abstractmethod
    def purge_job_ticks(
        self, job_origin_id: str, tick_status: JobTickStatus, before: datetime.datetime
    ):
        """Wipe ticks for a job for a certain status and timestamp.

        Args:
            job_origin_id (str): The id of the ExternalJob target to delete
            tick_status (JobTickStatus): The tick status to wipe
            before (datetime): All ticks before this datetime will get purged
        """

    @abc.abstractmethod
    def get_job_tick_stats(self, job_origin_id: str):
        """Get tick stats for a given job.

        Args:
            job_origin_id (str): The id of the ExternalJob target
        """

    @abc.abstractmethod
    def upgrade(self):
        """Perform any needed migrations"""

    def optimize_for_dagit(self, statement_timeout: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""

    def validate_stored_schedules(self, scheduler_class: Type):
        # Check for any running job states that reference a different scheduler,
        # prompt the user to wipe if they don't match
        stored_schedules = self.all_stored_job_state(job_type=JobType.SCHEDULE)

        for schedule in stored_schedules:
            if schedule.status != JobStatus.RUNNING:
                continue

            stored_scheduler_class = schedule.job_specific_data.scheduler

            if stored_scheduler_class and stored_scheduler_class != scheduler_class:
                instance_scheduler_class = scheduler_class if scheduler_class else "None"

                raise DagsterScheduleWipeRequired(
                    f"Found a running schedule using a scheduler ({stored_scheduler_class}) "
                    + f"that differs from the scheduler on the instance ({instance_scheduler_class}). "
                    + "The most likely reason for this error is that you changed the scheduler on "
                    + "your instance while it was still running schedules. "
                    + "To fix this, change the scheduler on your instance back to the previous "
                    + "scheduler configuration and run the command 'dagster schedule wipe'. It "
                    + f"will then be safe to change back to {instance_scheduler_class}."
                )
