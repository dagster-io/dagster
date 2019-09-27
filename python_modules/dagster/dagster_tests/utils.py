from dagster import DagsterInvariantViolationError, check
from dagster.core.scheduler import ScheduleStatus, Scheduler
from dagster.core.scheduler.storage import ScheduleStorage


class FilesytemTestScheduler(Scheduler):
    def __init__(self, artifacts_dir, schedule_storage):
        check.inst_param(schedule_storage, 'schedule_storage', ScheduleStorage)
        check.str_param(artifacts_dir, 'artifacts_dir')
        self._storage = schedule_storage
        self._artifacts_dir = artifacts_dir

    def all_schedules(self, status=None):
        return self._storage.all_schedules(status)

    def get_schedule_by_name(self, name):
        return self._storage.get_schedule_by_name(name)

    def start_schedule(self, schedule_name):
        schedule = self.get_schedule_by_name(schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to start schedule {name}, but it does not exist.'.format(
                    name=schedule_name
                )
            )

        if schedule.status == ScheduleStatus.RUNNING:
            raise DagsterInvariantViolationError(
                'You have attempted to start schedule {name}, but it is already running'.format(
                    name=schedule_name
                )
            )

        started_schedule = schedule.with_status(ScheduleStatus.RUNNING)
        self._storage.update_schedule(started_schedule)
        return schedule

    def stop_schedule(self, schedule_name):
        schedule = self.get_schedule_by_name(schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to stop schedule {name}, but was never initialized.'
                'Use `schedule up` to initialize schedules'.format(name=schedule_name)
            )

        if schedule.status == ScheduleStatus.STOPPED:
            raise DagsterInvariantViolationError(
                'You have attempted to stop schedule {name}, but it is already stopped'.format(
                    name=schedule_name
                )
            )

        stopped_schedule = schedule.with_status(ScheduleStatus.STOPPED)
        self._storage.update_schedule(stopped_schedule)
        return stopped_schedule

    def end_schedule(self, schedule_name):
        schedule = self.get_schedule_by_name(schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to end schedule {name}, but it is not running.'.format(
                    name=schedule_name
                )
            )

        self._storage.delete_schedule(schedule)
        return schedule
