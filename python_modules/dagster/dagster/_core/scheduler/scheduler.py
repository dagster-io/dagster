import abc
import os
from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple, Optional

from typing_extensions import Self

import dagster._check as check
from dagster._config import Field, IntSource
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.errors import DagsterError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import RemoteSchedule
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    ScheduleInstigatorData,
)
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._time import get_current_timestamp
from dagster._utils import mkdir_p


class DagsterSchedulerError(DagsterError):
    """Base class for all Dagster Scheduler errors."""


class DagsterScheduleDoesNotExist(DagsterSchedulerError):
    """Errors raised when fetching a schedule."""


class SchedulerDebugInfo(
    NamedTuple(
        "SchedulerDebugInfo",
        [
            ("errors", Sequence[str]),
            ("scheduler_config_info", str),
            ("scheduler_info", str),
            ("schedule_storage", Sequence[str]),
        ],
    )
):
    def __new__(
        cls,
        errors: Sequence[str],
        scheduler_config_info: str,
        scheduler_info: str,
        schedule_storage: Sequence[str],
    ):
        return super().__new__(
            cls,
            errors=check.sequence_param(errors, "errors", of_type=str),
            scheduler_config_info=check.str_param(scheduler_config_info, "scheduler_config_info"),
            scheduler_info=check.str_param(scheduler_info, "scheduler_info"),
            schedule_storage=check.sequence_param(
                schedule_storage, "schedule_storage", of_type=str
            ),
        )


class Scheduler(abc.ABC):
    """Abstract base class for a scheduler. This component is responsible for interfacing with
    an external system such as cron to ensure scheduled repeated execution according.
    """

    def start_schedule(
        self, instance: DagsterInstance, remote_schedule: RemoteSchedule
    ) -> InstigatorState:
        """Updates the status of the given schedule to `InstigatorStatus.RUNNING` in schedule storage,.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            remote_schedule (ExternalSchedule): The schedule to start

        """
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(remote_schedule, "remote_schedule", RemoteSchedule)

        stored_state = instance.get_instigator_state(
            remote_schedule.get_remote_origin_id(), remote_schedule.selector_id
        )
        computed_state = remote_schedule.get_current_instigator_state(stored_state)
        if computed_state.is_running:
            return computed_state

        new_instigator_data = ScheduleInstigatorData(
            remote_schedule.cron_schedule,
            get_current_timestamp(),
        )

        if not stored_state:
            started_state = InstigatorState(
                remote_schedule.get_remote_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.RUNNING,
                new_instigator_data,
            )
            instance.add_instigator_state(started_state)
        else:
            started_state = stored_state.with_status(InstigatorStatus.RUNNING).with_data(
                new_instigator_data
            )
            instance.update_instigator_state(started_state)
        return started_state

    def stop_schedule(
        self,
        instance: DagsterInstance,
        schedule_origin_id: str,
        schedule_selector_id: str,
        remote_schedule: Optional[RemoteSchedule],
    ) -> InstigatorState:
        """Updates the status of the given schedule to `InstigatorStatus.STOPPED` in schedule storage,.

        This should not be overridden by subclasses.

        Args:
            schedule_origin_id (string): The id of the schedule target to stop running.
        """
        check.str_param(schedule_origin_id, "schedule_origin_id")
        check.opt_inst_param(remote_schedule, "remote_schedule", RemoteSchedule)

        stored_state = instance.get_instigator_state(schedule_origin_id, schedule_selector_id)

        if not remote_schedule:
            computed_state = stored_state
        else:
            computed_state = remote_schedule.get_current_instigator_state(stored_state)

        if computed_state and not computed_state.is_running:
            return computed_state

        if not stored_state:
            assert remote_schedule
            stopped_state = InstigatorState(
                remote_schedule.get_remote_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.STOPPED,
                ScheduleInstigatorData(
                    remote_schedule.cron_schedule,
                ),
            )
            instance.add_instigator_state(stopped_state)
        else:
            stopped_state = stored_state.with_status(InstigatorStatus.STOPPED).with_data(
                ScheduleInstigatorData(
                    cron_schedule=computed_state.instigator_data.cron_schedule,  # type: ignore
                )
            )
            instance.update_instigator_state(stopped_state)

        return stopped_state

    def reset_schedule(
        self, instance: DagsterInstance, remote_schedule: RemoteSchedule
    ) -> InstigatorState:
        """If the given schedule has a default schedule status, then update the status to
        `InstigatorStatus.DECLARED_IN_CODE` in schedule storage.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            remote_schedule (ExternalSchedule): The schedule to reset.
        """
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(remote_schedule, "remote_schedule", RemoteSchedule)

        stored_state = instance.get_instigator_state(
            remote_schedule.get_remote_origin_id(), remote_schedule.selector_id
        )

        new_status = InstigatorStatus.DECLARED_IN_CODE

        if not stored_state:
            new_instigator_data = ScheduleInstigatorData(
                remote_schedule.cron_schedule,
                start_timestamp=None,
            )
            reset_state = instance.add_instigator_state(
                state=InstigatorState(
                    remote_schedule.get_remote_origin(),
                    InstigatorType.SCHEDULE,
                    new_status,
                    new_instigator_data,
                )
            )
        else:
            reset_state = instance.update_instigator_state(
                state=stored_state.with_status(new_status)
            )

        return reset_state

    @abc.abstractmethod
    def debug_info(self) -> str:
        """Returns debug information about the scheduler."""

    @abc.abstractmethod
    def get_logs_path(self, instance: DagsterInstance, schedule_origin_id: str) -> str:
        """Get path to store logs for schedule.

        Args:
            schedule_origin_id (string): The id of the schedule target to retrieve the log path for
        """


DEFAULT_MAX_CATCHUP_RUNS = 5


class DagsterDaemonScheduler(Scheduler, ConfigurableClass):
    """Default scheduler implementation that submits runs from the long-lived ``dagster-daemon``
    process. Periodically checks each running schedule for execution times that don't yet
    have runs and launches them.
    """

    def __init__(
        self,
        max_catchup_runs: int = DEFAULT_MAX_CATCHUP_RUNS,
        max_tick_retries: int = 0,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self.max_catchup_runs = check.opt_int_param(
            max_catchup_runs, "max_catchup_runs", DEFAULT_MAX_CATCHUP_RUNS
        )
        self.max_tick_retries = check.opt_int_param(max_tick_retries, "max_tick_retries", 0)
        self._inst_data = inst_data

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "max_catchup_runs": Field(
                IntSource,
                is_required=False,
                default_value=DEFAULT_MAX_CATCHUP_RUNS,
                description="""For partitioned schedules, controls the maximum number of past
            partitions for each schedule that will be considered when looking for missing
            runs . Generally this parameter will only come into play if the scheduler
            falls behind or launches after experiencing downtime. This parameter will not be checked for
            schedules without partition sets (for example, schedules created using the :py:func:`@schedule <dagster.schedule>` decorator) - only the most recent execution time will be considered for those schedules.

            Note: No matter what this value is, the scheduler will never launch a run from a time
            before the schedule was turned on, even if the schedule's ``start_date`` is earlier. If
            you want to launch runs for earlier partitions, `launch a backfill </concepts/partitions-schedules-sensors/backfills>`_.
            """,
            ),
            "max_tick_retries": Field(
                IntSource,
                default_value=0,
                is_required=False,
                description=(
                    "For each schedule tick that raises an error, the number of times to retry the tick."
                ),
            ),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    def debug_info(self) -> str:
        return ""

    def wipe(self, instance: DagsterInstance) -> None:
        pass

    def _get_or_create_logs_directory(
        self, instance: DagsterInstance, schedule_origin_id: str
    ) -> str:
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        logs_directory = os.path.join(instance.schedules_directory(), "logs", schedule_origin_id)
        if not os.path.isdir(logs_directory):
            mkdir_p(logs_directory)

        return logs_directory

    def get_logs_path(self, instance: DagsterInstance, schedule_origin_id: str) -> str:
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        logs_directory = self._get_or_create_logs_directory(instance, schedule_origin_id)
        return os.path.join(logs_directory, "scheduler.log")
