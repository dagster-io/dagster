import abc
import os
from collections import namedtuple
from datetime import datetime
from enum import Enum

import six

from dagster import check
from dagster.core.errors import DagsterError
from dagster.core.host_representation import ExternalSchedule
from dagster.core.instance import DagsterInstance
from dagster.core.origin import ScheduleOrigin
from dagster.serdes import ConfigurableClass, whitelist_for_serdes
from dagster.seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime
from dagster.utils import mkdir_p
from dagster.utils.error import SerializableErrorInfo


class DagsterSchedulerError(DagsterError):
    """Base class for all Dagster Scheduler errors"""


class DagsterScheduleReconciliationError(DagsterError):
    """Error raised during schedule state reconcilation. During reconcilation, exceptions that are
    raised when trying to start or stop a schedule are collected and passed to this wrapper exception.
    The individual exceptions can be accessed by the `errors` property. """

    def __init__(self, preamble, errors, *args, **kwargs):
        self.errors = errors

        error_msg = preamble
        error_messages = []
        for i_error, error in enumerate(self.errors):
            error_messages.append(str(error))
            error_msg += "\n    Error {i_error}: {error_message}".format(
                i_error=i_error + 1, error_message=str(error)
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(DagsterScheduleReconciliationError, self).__init__(error_msg, *args, **kwargs)


class DagsterScheduleDoesNotExist(DagsterSchedulerError):
    """Errors raised when ending a job for a schedule."""


@whitelist_for_serdes
class ScheduleStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ENDED = "ENDED"


def get_schedule_change_set(schedule_states, external_schedules):
    check.list_param(schedule_states, "schedule_states", ScheduleState)
    check.list_param(external_schedules, "external_schedules", ExternalSchedule)

    external_schedules_dict = {s.get_origin_id(): s for s in external_schedules}
    schedule_states_dict = {s.schedule_origin_id: s for s in schedule_states}

    external_schedule_origin_ids = set(external_schedules_dict.keys())
    schedule_state_ids = set(schedule_states_dict.keys())

    added_schedules = external_schedule_origin_ids - schedule_state_ids
    changed_schedules = external_schedule_origin_ids & schedule_state_ids
    removed_schedules = schedule_state_ids - external_schedule_origin_ids

    changeset = []

    for schedule_origin_id in added_schedules:
        changeset.append(
            ("add", external_schedules_dict[schedule_origin_id].name, schedule_origin_id, [])
        )

    for schedule_origin_id in changed_schedules:
        changes = []

        schedule_state = schedule_states_dict[schedule_origin_id]
        external_schedule = external_schedules_dict[schedule_origin_id]

        if schedule_state.cron_schedule != external_schedule.cron_schedule:
            changes.append(
                ("cron_schedule", (schedule_state.cron_schedule, external_schedule.cron_schedule))
            )

        if len(changes) > 0:
            changeset.append(
                (
                    "change",
                    external_schedules_dict[schedule_origin_id].name,
                    schedule_origin_id,
                    changes,
                )
            )

    for schedule_origin_id in removed_schedules:
        changeset.append(
            ("remove", schedule_states_dict[schedule_origin_id].name, schedule_origin_id, [])
        )

    return changeset


class SchedulerDebugInfo(
    namedtuple("SchedulerDebugInfo", "errors scheduler_config_info scheduler_info schedule_storage")
):
    def __new__(cls, errors, scheduler_config_info, scheduler_info, schedule_storage):
        return super(SchedulerDebugInfo, cls).__new__(
            cls,
            errors=check.list_param(errors, "errors", of_type=str),
            scheduler_config_info=check.str_param(scheduler_config_info, "scheduler_config_info"),
            scheduler_info=check.str_param(scheduler_info, "scheduler_info"),
            schedule_storage=check.list_param(schedule_storage, "schedule_storage", of_type=str),
        )


@whitelist_for_serdes
class ScheduleState(
    namedtuple("_StoredScheduleState", "origin status cron_schedule start_timestamp")
):
    def __new__(cls, origin, status, cron_schedule, start_timestamp=None):

        return super(ScheduleState, cls).__new__(
            cls,
            # Using the term "origin" to leave flexibility in handling future types
            check.inst_param(origin, "origin", ScheduleOrigin),
            check.inst_param(status, "status", ScheduleStatus),
            check.str_param(cron_schedule, "cron_schedule"),
            # Time in UTC at which the user started running the schedule (distinct from
            # `start_date` on partition-based schedules, which is used to define
            # the range of partitions)
            check.opt_float_param(start_timestamp, "start_timestamp"),
        )

    @property
    def name(self):
        return self.origin.schedule_name

    @property
    def pipeline_origin(self):
        # Set up for future proofing
        check.invariant(isinstance(self.origin, ScheduleOrigin))
        return self.origin

    @property
    def schedule_origin_id(self):
        return self.origin.get_id()

    @property
    def repository_origin_id(self):
        return self.origin.repository_origin.get_id()

    def with_status(self, status, start_time_utc=None):
        check.inst_param(status, "status", ScheduleStatus)
        check.opt_inst_param(start_time_utc, "start_time_utc", datetime)

        check.invariant(
            (status == ScheduleStatus.RUNNING) == (start_time_utc != None),
            "start_time_utc must be set if and only if the schedule is being started",
        )

        return ScheduleState(
            self.origin,
            status=status,
            cron_schedule=self.cron_schedule,
            start_timestamp=get_timestamp_from_utc_datetime(start_time_utc)
            if start_time_utc
            else None,
        )


class Scheduler(six.with_metaclass(abc.ABCMeta)):
    """Abstract base class for a scheduler. This component is responsible for interfacing with
    an external system such as cron to ensure scheduled repeated execution according.
    """

    def _get_schedule_state(self, instance, schedule_origin_id):
        schedule_state = instance.get_schedule_state(schedule_origin_id)
        if not schedule_state:
            raise DagsterScheduleDoesNotExist(
                "You have attempted to start the job for schedule id {id}, but its state is not in storage.".format(
                    id=schedule_origin_id
                )
            )

        return schedule_state

    def reconcile_scheduler_state(self, instance, external_repository):
        """Reconcile the ExternalSchedule list from the repository and ScheduleStorage
        on the instance to ensure there is a 1-1 correlation between ExternalSchedule and
        ScheduleStates, where the ExternalSchedule list is the source of truth.

        If a new ExternalSchedule is introduced, a new ScheduleState is added to storage with status
        ScheduleStatus.STOPPED.

        For every previously existing ExternalSchedule (where target id is the primary key),
        any changes to the definition are persisted in the corresponding ScheduleState and the status is
        left unchanged. The schedule is also restarted to make sure the external artifacts (such
        as a cron job) are up to date.

        For every ScheduleDefinitions that is removed, the corresponding ScheduleState is removed from
        the storage and the corresponding ScheduleState is ended.
        """

        schedules_to_restart = []
        for external_schedule in external_repository.get_external_schedules():
            # If a schedule already exists for schedule_def, overwrite bash script and
            # metadata file
            existing_schedule_state = instance.get_schedule_state(external_schedule.get_origin_id())
            if existing_schedule_state:

                new_timestamp = existing_schedule_state.start_timestamp
                if not new_timestamp and existing_schedule_state.status == ScheduleStatus.RUNNING:
                    new_timestamp = get_timestamp_from_utc_datetime(get_current_datetime_in_utc())

                # Keep the status, update target and cron schedule
                schedule_state = ScheduleState(
                    external_schedule.get_origin(),
                    existing_schedule_state.status,
                    external_schedule.cron_schedule,
                    new_timestamp,
                )

                instance.update_schedule_state(schedule_state)
                schedules_to_restart.append((existing_schedule_state, external_schedule))
            else:
                schedule_state = ScheduleState(
                    external_schedule.get_origin(),
                    ScheduleStatus.STOPPED,
                    external_schedule.cron_schedule,
                    start_timestamp=None,
                )

                instance.add_schedule_state(schedule_state)

        # Delete all existing schedules that are not in external schedules
        external_schedule_origin_ids = {
            s.get_origin_id() for s in external_repository.get_external_schedules()
        }
        existing_schedule_origin_ids = set(
            [
                s.schedule_origin_id
                for s in instance.all_stored_schedule_state(external_repository.get_origin_id())
            ]
        )
        schedule_origin_ids_to_delete = existing_schedule_origin_ids - external_schedule_origin_ids

        schedule_reconciliation_errors = []
        for schedule_state, external_schedule in schedules_to_restart:
            # Restart is only needed if the schedule was previously running
            if schedule_state.status == ScheduleStatus.RUNNING:
                try:
                    self.refresh_schedule(instance, external_schedule)
                except DagsterSchedulerError as e:
                    schedule_reconciliation_errors.append(e)

            if schedule_state.status == ScheduleStatus.STOPPED:
                try:
                    self.stop_schedule(instance, external_schedule.get_origin_id())
                except DagsterSchedulerError as e:
                    schedule_reconciliation_errors.append(e)

        for schedule_origin_id in schedule_origin_ids_to_delete:
            try:
                instance.stop_schedule_and_delete_from_storage(schedule_origin_id)
            except DagsterSchedulerError as e:
                schedule_reconciliation_errors.append(e)

        if len(schedule_reconciliation_errors):
            raise DagsterScheduleReconciliationError(
                "One or more errors were encountered by the Scheduler while starting or stopping schedules. "
                "Individual error messages follow:",
                errors=schedule_reconciliation_errors,
            )

    def start_schedule_and_update_storage_state(self, instance, external_schedule):
        """
        Updates the status of the given schedule to `ScheduleStatus.RUNNING` in schedule storage,
        then calls `start_schedule`.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            external_schedule (ExternalSchedule): The schedule to start

        """

        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        schedule_state = self._get_schedule_state(instance, external_schedule.get_origin_id())

        if schedule_state.status == ScheduleStatus.RUNNING:
            raise DagsterSchedulerError(
                "You have attempted to start schedule {name}, but it is already running".format(
                    name=external_schedule.name
                )
            )

        self.start_schedule(instance, external_schedule)
        started_schedule = schedule_state.with_status(
            ScheduleStatus.RUNNING, start_time_utc=get_current_datetime_in_utc()
        )
        instance.update_schedule_state(started_schedule)
        return started_schedule

    def stop_schedule_and_update_storage_state(self, instance, schedule_origin_id):
        """
        Updates the status of the given schedule to `ScheduleStatus.STOPPED` in schedule storage,
        then calls `stop_schedule`.

        This should not be overridden by subclasses.

        Args:
            schedule_origin_id (string): The id of the schedule target to stop running.
        """

        check.str_param(schedule_origin_id, "schedule_origin_id")

        schedule_state = self._get_schedule_state(instance, schedule_origin_id)

        self.stop_schedule(instance, schedule_origin_id)
        stopped_schedule = schedule_state.with_status(ScheduleStatus.STOPPED)
        instance.update_schedule_state(stopped_schedule)
        return stopped_schedule

    def stop_schedule_and_delete_from_storage(self, instance, schedule_origin_id):
        """
        Deletes a schedule from schedule storage, then calls `stop_schedule`.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            schedule_origin_id (string): The id of the schedule target to start running.
        """

        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        schedule = self._get_schedule_state(instance, schedule_origin_id)
        self.stop_schedule(instance, schedule_origin_id)
        instance.delete_schedule_state(schedule_origin_id)
        return schedule

    def refresh_schedule(self, instance, external_schedule):
        """Refresh a running schedule. This is called when user reconciles the schedule state.

        By default, this method will call stop_schedule and then start_schedule but can be
        overriden. For example, in the K8s Scheduler we patch the existing cronjob
        (without stopping it) to minimize downtime.

        Args:
            instance (DagsterInstance): The current instance.
            external_schedule (ExternalSchedule): The schedule to start running.
        """
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        self.stop_schedule(instance, external_schedule.get_origin_id())
        self.start_schedule(instance, external_schedule)

    @abc.abstractmethod
    def debug_info(self):
        """Returns debug information about the scheduler
        """

    @abc.abstractmethod
    def start_schedule(self, instance, external_schedule):
        """Start running a schedule. This method is called by `start_schedule_and_update_storage_state`,
        which first updates the status of the schedule in schedule storage to `ScheduleStatus.RUNNING`,
        then calls this method.

        For example, in the cron scheduler, this method writes a cron job to the cron tab
        for the given schedule.

        Args:
            instance (DagsterInstance): The current instance.
            external_schedule (ExternalSchedule): The schedule to start running.
        """

    @abc.abstractmethod
    def stop_schedule(self, instance, schedule_origin_id):
        """Stop running a schedule.

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
            schedule_origin_id (string): The id of the schedule target to stop running.
        """

    @abc.abstractmethod
    def running_schedule_count(self, instance, schedule_origin_id):
        """Returns the number of jobs currently running for the given schedule. This method is used
        for detecting when the scheduler is out of sync with schedule storage.

        For example, when:
        - There are duplicate jobs runnning for a single schedule
        - There are no jobs runnning for a schedule that is set to be running
        - There are still jobs running for a schedule that is set to be stopped

        When the scheduler and schedule storage are in sync, this method should return:
        - 1 when a schedule is set to be running
        - 0 when a schedule is set to be stopped

        Args:
            instance (DagsterInstance): The current instance.
            schedule_origin_id (string): The id of the schedule target to return the number of jobs for
        """

    @abc.abstractmethod
    def get_logs_path(self, instance, schedule_origin_id):
        """Get path to store logs for schedule

        Args:
            schedule_origin_id (string): The id of the schedule target to retrieve the log path for
        """


class DagsterCommandLineScheduler(Scheduler, ConfigurableClass):
    """Scheduler implementation that launches runs from the `dagster scheduler run`
    long-lived process.
    """

    def __init__(
        self, inst_data=None,
    ):
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return DagsterCommandLineScheduler(inst_data=inst_data)

    def debug_info(self):
        return ""

    def start_schedule(self, instance, external_schedule):
        # Automatically picked up by the `dagster scheduler run` command
        pass

    def stop_schedule(self, instance, schedule_origin_id):
        # Automatically picked up by the `dagster scheduler run` command
        pass

    def running_schedule_count(self, instance, schedule_origin_id):
        state = instance.get_schedule_state(schedule_origin_id)
        if not state:
            return 0
        return 1 if state.status == ScheduleStatus.RUNNING else 0

    def wipe(self, instance):
        pass

    def _get_or_create_logs_directory(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        logs_directory = os.path.join(instance.schedules_directory(), "logs", schedule_origin_id)
        if not os.path.isdir(logs_directory):
            mkdir_p(logs_directory)

        return logs_directory

    def get_logs_path(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        logs_directory = self._get_or_create_logs_directory(instance, schedule_origin_id)
        return os.path.join(logs_directory, "scheduler.log")


class ScheduleTickStatsSnapshot(
    namedtuple(
        "ScheduleTickStatsSnapshot", ("ticks_started ticks_succeeded ticks_skipped ticks_failed"),
    )
):
    def __new__(
        cls, ticks_started, ticks_succeeded, ticks_skipped, ticks_failed,
    ):
        return super(ScheduleTickStatsSnapshot, cls).__new__(
            cls,
            ticks_started=check.int_param(ticks_started, "ticks_started"),
            ticks_succeeded=check.int_param(ticks_succeeded, "ticks_succeeded"),
            ticks_skipped=check.int_param(ticks_skipped, "ticks_skipped"),
            ticks_failed=check.int_param(ticks_failed, "ticks_failed"),
        )


@whitelist_for_serdes
class ScheduleTickStatus(Enum):
    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


def _validate_schedule_tick_args(status, run_id=None, error=None):
    check.inst_param(status, "status", ScheduleTickStatus)

    if status == ScheduleTickStatus.SUCCESS:
        check.str_param(run_id, "run_id")
        check.invariant(
            error is None, desc="Schedule tick status is SUCCESS, but error was provided"
        )
    elif status == ScheduleTickStatus.FAILURE:
        check.inst_param(error, "error", SerializableErrorInfo)
    else:
        check.invariant(
            error is None, "Schedule tick status was not FAILURE but error was provided"
        )


@whitelist_for_serdes
class ScheduleTickData(
    namedtuple(
        "Schedule", "schedule_origin_id schedule_name cron_schedule timestamp status run_id error"
    )
):
    def __new__(
        cls,
        schedule_origin_id,
        schedule_name,
        cron_schedule,
        timestamp,
        status,
        run_id=None,
        error=None,
    ):
        """
        This class defines the data that is serialized and stored in ``ScheduleStorage``. We depend
        on the schedule storage implementation to provide schedule tick ids, and therefore
        separate all other data into this serializable class that can be stored independently of the
        id

        Arguments:
            schedule_origin_id (str): The id of the schedule target for this tick
            schedule_name (str): The name of the schedule for this tick
            cron_schedule (str): The cron schedule of the ``ScheduleDefinition`` for tracking
                purposes. This is helpful when debugging changes in the cron schedule.
            timestamp (float): The timestamp at which this schedule execution started
            status (ScheduleTickStatus): The status of the tick, which can be updated

        Keyword Arguments:
            run_id (str): The run created by the tick.
            error (SerializableErrorInfo): The error caught during schedule execution. This is set
                only when the status is ``ScheduleTickStatus.Failure``
        """

        _validate_schedule_tick_args(status, run_id, error)
        return super(ScheduleTickData, cls).__new__(
            cls,
            check.str_param(schedule_origin_id, "schedule_origin_id"),
            check.str_param(schedule_name, "schedule_name"),
            check.opt_str_param(cron_schedule, "cron_schedule"),
            check.float_param(timestamp, "timestamp"),
            status,
            run_id,
            error,
        )

    def with_status(self, status, run_id=None, error=None, cron_schedule=None):
        check.inst_param(status, "status", ScheduleTickStatus)
        return ScheduleTickData(
            schedule_origin_id=self.schedule_origin_id,
            schedule_name=self.schedule_name,
            cron_schedule=cron_schedule if cron_schedule is not None else self.cron_schedule,
            timestamp=self.timestamp,
            status=status,
            run_id=run_id if run_id is not None else self.run_id,
            error=error if error is not None else self.error,
        )


class ScheduleTick(namedtuple("Schedule", "tick_id schedule_tick_data")):
    """
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
    """

    def __new__(cls, tick_id, schedule_tick_data):
        return super(ScheduleTick, cls).__new__(
            cls,
            check.int_param(tick_id, "tick_id"),
            check.inst_param(schedule_tick_data, "schedule_tick_data", ScheduleTickData),
        )

    def with_status(self, status, run_id=None, error=None, cron_schedule=None):
        check.inst_param(status, "status", ScheduleTickStatus)
        return self._replace(
            schedule_tick_data=self.schedule_tick_data.with_status(
                status, run_id=run_id, error=error, cron_schedule=cron_schedule
            )
        )

    @property
    def schedule_origin_id(self):
        return self.schedule_tick_data.schedule_origin_id

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
