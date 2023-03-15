import abc
import os
from typing import Any, Mapping, NamedTuple, Optional, Sequence

from typing_extensions import Self

import dagster._check as check
from dagster._config import Field, IntSource
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.errors import DagsterError
from dagster._core.host_representation import ExternalSchedule
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    ScheduleInstigatorData,
)
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._seven import get_current_datetime_in_utc
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
        return super(SchedulerDebugInfo, cls).__new__(
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
        self, instance: DagsterInstance, external_schedule: ExternalSchedule
    ) -> InstigatorState:
        """Updates the status of the given schedule to `InstigatorStatus.RUNNING` in schedule storage,.

        This should not be overridden by subclasses.

        Args:
            instance (DagsterInstance): The current instance.
            external_schedule (ExternalSchedule): The schedule to start

        """
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        stored_state = instance.get_instigator_state(
            external_schedule.get_external_origin_id(), external_schedule.selector_id
        )
        computed_state = external_schedule.get_current_instigator_state(stored_state)
        if computed_state.is_running:
            return computed_state

        new_instigator_data = ScheduleInstigatorData(
            external_schedule.cron_schedule,
            get_current_datetime_in_utc().timestamp(),
        )

        if not stored_state:
            started_state = InstigatorState(
                external_schedule.get_external_origin(),
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
        external_schedule: Optional[ExternalSchedule],
    ) -> InstigatorState:
        """Updates the status of the given schedule to `InstigatorStatus.STOPPED` in schedule storage,.

        This should not be overridden by subclasses.

        Args:
            schedule_origin_id (string): The id of the schedule target to stop running.
        """
        check.str_param(schedule_origin_id, "schedule_origin_id")
        check.opt_inst_param(external_schedule, "external_schedule", ExternalSchedule)

        stored_state = instance.get_instigator_state(schedule_origin_id, schedule_selector_id)

        if not external_schedule:
            computed_state = stored_state
        else:
            computed_state = external_schedule.get_current_instigator_state(stored_state)

        if computed_state and not computed_state.is_running:
            return computed_state

        if not stored_state:
            assert external_schedule
            stopped_state = InstigatorState(
                external_schedule.get_external_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.STOPPED,
                ScheduleInstigatorData(
                    external_schedule.cron_schedule,
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
    """Default scheduler implementation that submits runs from the `dagster-daemon`
    long-lived process. Periodically checks each running schedule for execution times that don't
    have runs yet and launches them.
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
            schedules without partition sets (for example, schedules created using the @schedule
            decorator) - only the most recent execution time will be considered for those schedules.

            Note that no matter what this value is, the scheduler will never launch a run from a time
            before the schedule was turned on (even if the start_date on the schedule is earlier) - if
            you want to launch runs for earlier partitions, launch a backfill.
            """,
            ),
            "max_tick_retries": Field(
                IntSource,
                default_value=0,
                is_required=False,
                description=(
                    "For each schedule tick that raises an error, how many times to retry that tick"
                ),
            ),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return DagsterDaemonScheduler(inst_data=inst_data, **config_value)

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
