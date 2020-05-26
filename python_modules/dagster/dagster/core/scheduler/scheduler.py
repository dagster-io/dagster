import abc
from collections import namedtuple
from enum import Enum

import six

from dagster import check
from dagster.core.definitions.repository import RepositoryDefinition
from dagster.core.definitions.schedule import ScheduleDefinition, ScheduleDefinitionData
from dagster.core.errors import DagsterError
from dagster.core.instance import DagsterInstance
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


class DagsterSchedulerError(DagsterError):
    '''Base class for all Dagster Scheduler errors'''


class DagsterScheduleReconciliationError(DagsterError):
    '''Error raised during schedule state reconcilation. During reconcilation, exceptions that are
    raised when trying to start or stop a schedule are collected and passed to this wrapper exception.
    The individual exceptions can be accessed by the `errors` property. '''

    def __init__(self, preamble, errors, *args, **kwargs):
        self.errors = errors

        error_msg = preamble
        error_messages = []
        for i_error, error in enumerate(self.errors):
            error_messages.append(str(error))
            error_msg += '\n    Error {i_error}: {error_message}'.format(
                i_error=i_error + 1, error_message=str(error)
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(DagsterScheduleReconciliationError, self).__init__(error_msg, *args, **kwargs)


class DagsterScheduleDoesNotExist(DagsterSchedulerError):
    '''Errors raised when ending a job for a schedule.'''


@whitelist_for_serdes
class ScheduleStatus(Enum):
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ENDED = 'ENDED'


def get_schedule_change_set(old_schedules, new_schedule_defs):
    check.list_param(old_schedules, 'old_schedules', Schedule)
    check.list_param(new_schedule_defs, 'new_schedule_defs', ScheduleDefinition)

    new_schedules_defs_dict = {s.name: s for s in new_schedule_defs}
    old_schedules_dict = {s.name: s for s in old_schedules}

    new_schedule_defs_names = set(new_schedules_defs_dict.keys())
    old_schedules_names = set(old_schedules_dict.keys())

    added_schedules = new_schedule_defs_names - old_schedules_names
    changed_schedules = new_schedule_defs_names & old_schedules_names
    removed_schedules = old_schedules_names - new_schedule_defs_names

    changeset = []

    for schedule_name in added_schedules:
        changeset.append(("add", schedule_name, []))

    for schedule_name in changed_schedules:
        changes = []

        old_schedule_def = old_schedules_dict[schedule_name].schedule_definition_data
        new_schedule_def = new_schedules_defs_dict[schedule_name]

        if old_schedule_def.cron_schedule != new_schedule_def.cron_schedule:
            changes.append(
                ("cron_schedule", (old_schedule_def.cron_schedule, new_schedule_def.cron_schedule))
            )

        if len(changes) > 0:
            changeset.append(("change", schedule_name, changes))

    for schedule_name in removed_schedules:
        changeset.append(("remove", schedule_name, []))

    return changeset


class SchedulerDebugInfo(
    namedtuple('SchedulerDebugInfo', 'errors scheduler_config_info scheduler_info schedule_storage')
):
    def __new__(cls, errors, scheduler_config_info, scheduler_info, schedule_storage):
        return super(SchedulerDebugInfo, cls).__new__(
            cls,
            errors=check.list_param(errors, 'errors', of_type=str),
            scheduler_config_info=check.str_param(scheduler_config_info, 'scheduler_config_info'),
            scheduler_info=check.str_param(scheduler_info, 'scheduler_info'),
            schedule_storage=check.list_param(schedule_storage, 'schedule_storage', of_type=str),
        )


class SchedulerHandle(object):
    def __init__(
        self, schedule_defs,
    ):
        check.list_param(schedule_defs, 'schedule_defs', ScheduleDefinition)
        self.schedule_defs = schedule_defs


@whitelist_for_serdes
class Schedule(
    namedtuple('Schedule', 'schedule_definition_data status python_path repository_path')
):
    def __new__(cls, schedule_definition_data, status, python_path=None, repository_path=None):

        return super(Schedule, cls).__new__(
            cls,
            check.inst_param(
                schedule_definition_data, 'schedule_definition_data', ScheduleDefinitionData
            ),
            check.inst_param(status, 'status', ScheduleStatus),
            check.opt_str_param(python_path, 'python_path'),
            check.opt_str_param(repository_path, 'repository_path'),
        )

    @property
    def name(self):
        return self.schedule_definition_data.name

    @property
    def cron_schedule(self):
        return self.schedule_definition_data.cron_schedule

    @property
    def environment_vars(self):
        return self.schedule_definition_data.environment_vars

    def with_status(self, status):
        check.inst_param(status, 'status', ScheduleStatus)

        return Schedule(
            self.schedule_definition_data,
            status=status,
            python_path=self.python_path,
            repository_path=self.repository_path,
        )


class Scheduler(six.with_metaclass(abc.ABCMeta)):
    '''Abstract base class for a scheduler. This component is responsible for interfacing with
    an external system such as cron to ensure scheduled repeated execution according.
    '''

    def _get_schedule_by_name(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterScheduleDoesNotExist(
                'You have attempted to start the job for schedule {name}, but it does not exist.'.format(
                    name=schedule_name
                )
            )

        return schedule

    def reconcile_scheduler_state(self, instance, repository, python_path, repository_path):
        '''Reconcile the ScheduleDefinitions list from the repository and ScheduleStorage
        on the instance to ensure there is a 1-1 correlation between ScheduleDefinitions and

        Schedules, where the ScheduleDefinitions list is the source of truth.

        If a new ScheduleDefinition is introduced, a new Schedule is added to storage with status
        ScheduleStatus.STOPPED.

        For every previously existing ScheduleDefinition (where schedule_name is the primary key),
        any changes to the definition are persisted in the corresponding Schedule and the status is
        left unchanged. The schedule is also restarted to make sure the external artifacts (such
        as a cron job) are up to date.

        For every ScheduleDefinitions that is removed, the corresponding Schedule is removed from
        the storage and the corresponding Schedule is ended.
        '''

        schedules_to_restart = []
        for schedule_def in repository.schedule_defs:
            # If a schedule already exists for schedule_def, overwrite bash script and
            # metadata file
            existing_schedule = instance.get_schedule_by_name(repository, schedule_def.name)
            if existing_schedule:
                # Keep the status, but replace schedule_def, python_path, and repository_path
                schedule = Schedule(
                    schedule_def.schedule_definition_data,
                    existing_schedule.status,
                    python_path,
                    repository_path,
                )

                instance.update_schedule(repository, schedule)
                schedules_to_restart.append(schedule)
            else:
                schedule = Schedule(
                    schedule_def.schedule_definition_data,
                    ScheduleStatus.STOPPED,
                    python_path,
                    repository_path,
                )

                instance.add_schedule(repository, schedule)

        # Delete all existing schedules that are not in schedule_defs
        schedule_def_names = {s.name for s in repository.schedule_defs}
        existing_schedule_names = set([s.name for s in instance.all_schedules(repository)])
        schedule_names_to_delete = existing_schedule_names - schedule_def_names

        schedule_reconciliation_errors = []
        for schedule in schedules_to_restart:
            # Restart is only needed if the schedule was previously running
            if schedule.status == ScheduleStatus.RUNNING:
                try:
                    self.stop_schedule(instance, repository, schedule.name)
                    self.start_schedule(instance, repository, schedule.name)
                except DagsterSchedulerError as e:
                    schedule_reconciliation_errors.append(e)

            if schedule.status == ScheduleStatus.STOPPED:
                try:
                    self.stop_schedule(instance, repository, schedule.name)
                except DagsterSchedulerError as e:
                    schedule_reconciliation_errors.append(e)

        for schedule_name in schedule_names_to_delete:
            try:
                instance.stop_schedule_and_delete_from_storage(repository, schedule_name)
            except DagsterSchedulerError as e:
                schedule_reconciliation_errors.append(e)

        if len(schedule_reconciliation_errors):
            raise DagsterScheduleReconciliationError(
                "One or more errors were encountered by the Scheduler while starting or stopping schedules. "
                "Individual error messages follow:",
                errors=schedule_reconciliation_errors,
            )

    def start_schedule_and_update_storage_state(self, instance, repository, schedule_name):
        '''
        Updates the status of the given schedule to `ScheduleStatus.RUNNING` in schedule storage,
        then calls `start_schedule`.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            repository (RepositoryDefinition): The repository containing the schedule definition.
            schedule_name (string): The name of the schedule to start running.
        '''

        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')

        schedule = self._get_schedule_by_name(instance, repository, schedule_name)

        if schedule.status == ScheduleStatus.RUNNING:
            raise DagsterSchedulerError(
                'You have attempted to start schedule {name}, but it is already running'.format(
                    name=schedule_name
                )
            )

        self.start_schedule(instance, repository, schedule.name)
        started_schedule = schedule.with_status(ScheduleStatus.RUNNING)
        instance.update_schedule(repository, started_schedule)
        return started_schedule

    def stop_schedule_and_update_storage_state(self, instance, repository, schedule_name):
        '''
        Updates the status of the given schedule to `ScheduleStatus.STOPPED` in schedule storage,
        then calls `stop_schedule`.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            repository (RepositoryDefinition): The repository containing the schedule definition.
            schedule_name (string): The name of the schedule to start running.
        '''

        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')

        schedule = self._get_schedule_by_name(instance, repository, schedule_name)

        self.stop_schedule(instance, repository, schedule.name)
        stopped_schedule = schedule.with_status(ScheduleStatus.STOPPED)
        instance.update_schedule(repository, stopped_schedule)
        return stopped_schedule

    def stop_schedule_and_delete_from_storage(self, instance, repository, schedule_name):
        '''
        Deletes a schedule from schedule storage, then calls `stop_schedule`.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            repository (RepositoryDefinition): The repository containing the schedule definition.
            schedule_name (string): The name of the schedule to start running.
        '''

        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')

        schedule = self._get_schedule_by_name(instance, repository, schedule_name)
        self.stop_schedule(instance, repository, schedule.name)
        instance.delete_schedule(repository, schedule)
        return schedule

    @abc.abstractmethod
    def debug_info(self):
        '''Returns debug information about the scheduler
        '''

    @abc.abstractmethod
    def start_schedule(self, instance, repository, schedule_name):
        '''Start running a schedule. This method is called by `start_schedule_and_update_storage_state`,
        which first updates the status of the schedule in schedule storage to `ScheduleStatus.RUNNING`,
        then calls this method.

        For example, in the cron scheduler, this method writes a cron job to the cron tab
        for the given schedule.

        Args:
            instance (DagsterInstance): The current instance.
            repository (RepositoryDefinition): The repository containing the schedule definition.
            schedule_name (string): The name of the schedule to start running.
        '''

    @abc.abstractmethod
    def stop_schedule(self, instance, repository, schedule_name):
        '''Stop running a schedule.

        This method is called by
        1) `stop_schedule_and_update_storage_state`,
        which first updates the status of the schedule in schedule storage to `ScheduleStatus.STOPPED`,
        then calls this method.
        2) `stop_schedule_and_delete_from_storage`, which deletes the schedule from schedule storage
        then calls this method.

        For example, in the cron scheduler, this method deletes the cron job for a given scheduler
        from the cron tab.

        Args:
            instance (DagsterInstance): The current instance.
            repository (RepositoryDefinition): The repository containing the schedule definition.
            schedule_name (string): The schedule to stop running.
        '''

    @abc.abstractmethod
    def running_schedule_count(self, repository_name, schedule_name):
        '''Returns the number of jobs currently running for the given schedule. This method is used
        for detecting when the scheduler is out of sync with schedule storage.

        For example, when:
        - There are duplicate jobs runnning for a single schedule
        - There are no jobs runnning for a schedule that is set to be running
        - There are still jobs running for a schedule that is set to be stopped

        When the scheduler and schedule storage are in sync, this method should return:
        - 1 when a schedule is set to be running
        - 0 wen a schedule is set to be stopped

        Args:
            repository_name (string): The name of the repository containing the schedule definition.
            schedule_name (string): The schedule to return the number of jobs for
        '''

    @abc.abstractmethod
    def get_logs_path(self, instance, repository, schedule_name):
        '''Get path to scheduler logs for schedule
        '''

    @abc.abstractmethod
    def get_logs_directory(self, instance, repository, schedule_name):
        '''Get directory that stores logs for schedule
        '''


class ScheduleTickStatsSnapshot(
    namedtuple(
        'ScheduleTickStatsSnapshot', ('ticks_started ticks_succeeded ticks_skipped ticks_failed'),
    )
):
    def __new__(
        cls, ticks_started, ticks_succeeded, ticks_skipped, ticks_failed,
    ):
        return super(ScheduleTickStatsSnapshot, cls).__new__(
            cls,
            ticks_started=check.int_param(ticks_started, 'ticks_started'),
            ticks_succeeded=check.int_param(ticks_succeeded, 'ticks_succeeded'),
            ticks_skipped=check.int_param(ticks_skipped, 'ticks_skipped'),
            ticks_failed=check.int_param(ticks_failed, 'ticks_failed'),
        )


@whitelist_for_serdes
class ScheduleTickStatus(Enum):
    STARTED = 'STARTED'
    SKIPPED = 'SKIPPED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


def _validate_schedule_tick_args(status, run_id=None, error=None):
    check.inst_param(status, 'status', ScheduleTickStatus)

    if status == ScheduleTickStatus.SUCCESS:
        check.str_param(run_id, 'run_id')
        check.invariant(
            error is None, desc="Schedule tick status is SUCCESS, but error was provided"
        )
    elif status == ScheduleTickStatus.FAILURE:
        check.invariant(run_id is None, "Schedule tick status is FAILURE but run_id was provided")
        check.inst_param(error, 'error', SerializableErrorInfo)
    else:
        check.invariant(
            run_id is None, "Schedule tick status was not SUCCESS, but run_id was provided"
        )
        check.invariant(
            error is None, "Schedule tick status was not FAILURE but error was provided"
        )


@whitelist_for_serdes
class ScheduleTickData(
    namedtuple('Schedule', 'schedule_name cron_schedule timestamp status run_id error')
):
    def __new__(cls, schedule_name, cron_schedule, timestamp, status, run_id=None, error=None):
        '''
        This class defines the data that is serialized and stored in ``ScheduleStorage``. We depend
        on the schedule storage implementation to provide schedule tick ids, and therefore
        separate all other data into this serializable class that can be stored independently of the
        id

        Arguments:
            schedule_name (str): The name of the schedule for this tick
            cron_schedule (str): The cron schedule of the ``ScheduleDefinition`` for tracking
                purposes. This is helpful when debugging changes in the cron schedule.
            timestamp (float): The timestamp at which this schedule execution started
            status (ScheduleTickStatus): The status of the tick, which can be updated

        Keyword Arguments:
            run_id (str): The run created by the tick. This is set only when the status is
                ``ScheduleTickStatus.SUCCESS``
            error (SerializableErrorInfo): The error caught during schedule execution. This is set
                only when the status is ``ScheduleTickStatus.Failure``
        '''

        _validate_schedule_tick_args(status, run_id, error)
        return super(ScheduleTickData, cls).__new__(
            cls,
            check.str_param(schedule_name, 'schedule_name'),
            check.str_param(cron_schedule, 'cron_schedule'),
            check.float_param(timestamp, 'timestamp'),
            status,
            run_id,
            error,
        )

    def with_status(self, status, run_id=None, error=None):
        check.inst_param(status, 'status', ScheduleTickStatus)
        return self._replace(status=status, run_id=run_id, error=error)


class ScheduleTick(namedtuple('Schedule', 'tick_id schedule_tick_data')):
    '''
    A scheduler is configured to run at an multiple intervals set by the `cron_schedule`
    properties on ``ScheduleDefinition``. We define a schedule tick as each time the scheduler
    runs for a specific schedule.

    When the schedule is being executed to create a pipeline run, we create a``ScheduleTick``
    object and store it in ``ScheduleStorage``. This is needed because not every tick results
    in creating a run, due to skips or errors.

    At the beginning of schedule execution, we create a ``ScheduleTick`` object in the
    ``ScheduleTickStatus.STARTED`` state.

    A schedule definition has a `should_execute` argument, where users can define a function
    which defines whether to create a run for the current tick. In the case where
    ``should_execute`` returns false, schedule execution is short-circuited, a run is not created,
    and the status of the schedule tick is updated to be ``ScheduleTickStatus.SKIPPED``.

    There are also several errors that can occur during schedule execution, which are important
    to track for observability and alerting. There are several user defined functions that
    are run during schedule execution, which are each wrapped with a ``user_error_boundary``.
    There is also the possibility of a framework error. These errors are caught,
    serialized, and stored on the ``ScheduleTick``.
    '''

    def __new__(cls, tick_id, schedule_tick_data):
        return super(ScheduleTick, cls).__new__(
            cls,
            check.int_param(tick_id, 'tick_id'),
            check.inst_param(schedule_tick_data, 'schedule_tick_data', ScheduleTickData),
        )

    def with_status(self, status, run_id=None, error=None):
        check.inst_param(status, 'status', ScheduleTickStatus)
        return self._replace(
            schedule_tick_data=self.schedule_tick_data.with_status(status, run_id, error)
        )

    @property
    def schedule_name(self):
        return self.schedule_tick_data.schedule_name

    @property
    def cron_schedule(self):
        return self.schedule_tick_data.cron_schedule

    @property
    def timestamp(self):
        return self.schedule_tick_data.timestamp

    @property
    def status(self):
        return self.schedule_tick_data.status

    @property
    def run_id(self):
        return self.schedule_tick_data.run_id

    @property
    def error(self):
        return self.schedule_tick_data.error
