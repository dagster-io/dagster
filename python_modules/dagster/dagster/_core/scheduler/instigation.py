from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import AbstractSet, Any, Generic, NamedTuple, Optional, Union  # noqa: UP035

from dagster_shared.serdes import EnumSerializer, deserialize_value, whitelist_for_serdes
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions import RunRequest
from dagster._core.definitions.asset_key import T_EntityKey, entity_key_from_db_string
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluationWithRunIds,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

# re-export
from dagster._core.definitions.run_request import (
    InstigatorType as InstigatorType,
    SkipReason as SkipReason,
)
from dagster._core.definitions.selector import InstigatorSelector, RepositorySelector
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.remote_representation.origin import RemoteInstigatorOrigin
from dagster._serdes import create_snapshot_id
from dagster._time import get_current_timestamp, utc_datetime_from_naive
from dagster._utils import xor
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.merger import merge_dicts

InstigatorData: TypeAlias = Union["ScheduleInstigatorData", "SensorInstigatorData"]


class InstigatorStatusBackcompatSerializer(EnumSerializer):
    def unpack(self, value: str):
        if value == InstigatorStatus.AUTOMATICALLY_RUNNING.name:
            value = InstigatorStatus.DECLARED_IN_CODE.name

        return super().unpack(value)


@whitelist_for_serdes(
    serializer=InstigatorStatusBackcompatSerializer,
    old_storage_names={"JobStatus"},
)
class InstigatorStatus(Enum):
    # User has taken some manual action to change the status of the run instigator
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"

    # The run instigator status is controlled by its default setting in code
    DECLARED_IN_CODE = "DECLARED_IN_CODE"

    # DEPRECATED: use InstigatorStatus.DECLARED_IN_CODE
    AUTOMATICALLY_RUNNING = "AUTOMATICALLY_RUNNING"


@whitelist_for_serdes
class DynamicPartitionsRequestResult(
    NamedTuple(
        "_DynamicPartitionsRequestResult",
        [
            ("partitions_def_name", str),
            ("added_partitions", Optional[Sequence[str]]),
            ("deleted_partitions", Optional[Sequence[str]]),
            ("skipped_partitions", Sequence[str]),
        ],
    )
):
    def __new__(
        cls,
        partitions_def_name: str,
        added_partitions: Optional[Sequence[str]],
        deleted_partitions: Optional[Sequence[str]],
        skipped_partitions: Sequence[str],
    ):
        check.opt_sequence_param(added_partitions, "added_partitions")
        check.opt_sequence_param(deleted_partitions, "deleted_partitions")

        # One of added_partitions or deleted_partitions must be a sequence, and the other must be None
        if not xor(added_partitions is None, deleted_partitions is None):
            check.failed("Exactly one of added_partitions and deleted_partitions must be provided")

        return super().__new__(
            cls,
            check.str_param(partitions_def_name, "partitions_def_name"),
            added_partitions,
            deleted_partitions,
            check.sequence_param(skipped_partitions, "skipped_partitions"),
        )


@whitelist_for_serdes(old_storage_names={"SensorJobData"})
class SensorInstigatorData(
    NamedTuple(
        "_SensorInstigatorData",
        [
            # the last completed tick timestamp, exposed to the context as a deprecated field
            ("last_tick_timestamp", Optional[float]),
            ("last_run_key", Optional[str]),
            ("min_interval", Optional[int]),
            ("cursor", Optional[str]),
            # the last time a tick was initiated, used to prevent issuing multiple threads from
            # evaluating ticks within the minimum interval
            ("last_tick_start_timestamp", Optional[float]),
            # the last time the sensor was started
            ("last_sensor_start_timestamp", Optional[float]),
            ("sensor_type", Optional[SensorType]),
            # the last time the tick completed evaluation, used to detect cases where ticks are
            # interrupted part way through
            ("last_tick_success_timestamp", Optional[float]),
        ],
    )
):
    def __new__(
        cls,
        last_tick_timestamp: Optional[float] = None,
        last_run_key: Optional[str] = None,
        min_interval: Optional[int] = None,
        cursor: Optional[str] = None,
        last_tick_start_timestamp: Optional[float] = None,
        last_sensor_start_timestamp: Optional[float] = None,
        sensor_type: Optional[SensorType] = None,
        last_tick_success_timestamp: Optional[float] = None,
    ):
        return super().__new__(
            cls,
            check.opt_float_param(last_tick_timestamp, "last_tick_timestamp"),
            check.opt_str_param(last_run_key, "last_run_key"),
            check.opt_int_param(min_interval, "min_interval"),
            check.opt_str_param(cursor, "cursor"),
            check.opt_float_param(last_tick_start_timestamp, "last_tick_start_timestamp"),
            check.opt_float_param(last_sensor_start_timestamp, "last_sensor_start_timestamp"),
            check.opt_inst_param(sensor_type, "sensor_type", SensorType),
            check.opt_float_param(last_tick_success_timestamp, "last_tick_success_timestamp"),
        )

    def with_sensor_start_timestamp(self, start_timestamp: float) -> "SensorInstigatorData":
        check.float_param(start_timestamp, "start_timestamp")
        return SensorInstigatorData(
            self.last_tick_timestamp,
            self.last_run_key,
            self.min_interval,
            self.cursor,
            self.last_tick_start_timestamp,
            start_timestamp,
            self.sensor_type,
            self.last_tick_success_timestamp,
        )


@whitelist_for_serdes(old_storage_names={"ScheduleJobData"})
class ScheduleInstigatorData(
    NamedTuple(
        "_ScheduleInstigatorData",
        [
            ("cron_schedule", Union[str, Sequence[str]]),
            ("start_timestamp", Optional[float]),
            ("last_iteration_timestamp", Optional[float]),
        ],
    )
):
    # removed scheduler, 1/5/2022 (0.13.13)
    def __new__(
        cls,
        cron_schedule: Union[str, Sequence[str]],
        start_timestamp: Optional[float] = None,
        last_iteration_timestamp: Optional[float] = None,
    ):
        cron_schedule = check.inst_param(cron_schedule, "cron_schedule", (str, list))
        if not isinstance(cron_schedule, str):
            cron_schedule = check.sequence_param(cron_schedule, "cron_schedule", of_type=str)

        return super().__new__(
            cls,
            cron_schedule,
            # Time in UTC at which the user started running the schedule (distinct from
            # `start_date` on partition-based schedules, which is used to define
            # the range of partitions)
            check.opt_float_param(start_timestamp, "start_timestamp"),
            # Time in UTC at which the schedule was last evaluated.  This enables the cron schedule
            # to change for running schedules and the previous iteration is not backfilled.
            check.opt_float_param(last_iteration_timestamp, "last_iteration_timestamp"),
        )


def check_instigator_data(
    instigator_type: InstigatorType,
    instigator_data: Optional[InstigatorData],
) -> Optional[InstigatorData]:
    if instigator_type == InstigatorType.SCHEDULE:
        check.inst_param(instigator_data, "instigator_data", ScheduleInstigatorData)
    elif instigator_type == InstigatorType.SENSOR:
        check.opt_inst_param(instigator_data, "instigator_data", SensorInstigatorData)
    else:
        check.failed(
            f"Unexpected instigator type {instigator_type}, expected one of InstigatorType.SENSOR,"
            " InstigatorType.SCHEDULE"
        )

    return instigator_data


@whitelist_for_serdes(
    old_storage_names={"JobState"},
    storage_field_names={
        "instigator_type": "job_type",
        "instigator_data": "job_specific_data",
    },
)
class InstigatorState(
    NamedTuple(
        "_InstigationState",
        [
            ("origin", RemoteInstigatorOrigin),
            ("instigator_type", InstigatorType),
            ("status", InstigatorStatus),
            ("instigator_data", Optional[InstigatorData]),
        ],
    )
):
    def __new__(
        cls,
        origin: RemoteInstigatorOrigin,
        instigator_type: InstigatorType,
        status: InstigatorStatus,
        instigator_data: Optional[InstigatorData] = None,
    ):
        return super().__new__(
            cls,
            check.inst_param(origin, "origin", RemoteInstigatorOrigin),
            check.inst_param(instigator_type, "instigator_type", InstigatorType),
            check.inst_param(status, "status", InstigatorStatus),
            check_instigator_data(instigator_type, instigator_data),
        )

    @property
    def is_running(self) -> bool:
        return self.status != InstigatorStatus.STOPPED

    @property
    def name(self) -> str:
        return self.origin.instigator_name

    @property
    def instigator_name(self) -> str:
        return self.origin.instigator_name

    @property
    def repository_origin_id(self) -> str:
        return self.origin.repository_origin.get_id()

    @property
    def repository_selector(self) -> RepositorySelector:
        return RepositorySelector(
            location_name=self.origin.repository_origin.code_location_origin.location_name,
            repository_name=self.origin.repository_origin.repository_name,
        )

    @property
    def repository_selector_id(self) -> str:
        return create_snapshot_id(self.repository_selector)

    @property
    def instigator_origin_id(self) -> str:
        return self.origin.get_id()

    @property
    def selector_id(self) -> str:
        return create_snapshot_id(
            InstigatorSelector(
                location_name=self.origin.repository_origin.code_location_origin.location_name,
                repository_name=self.origin.repository_origin.repository_name,
                name=self.origin.instigator_name,
            )
        )

    def with_status(self, status: InstigatorStatus) -> "InstigatorState":
        check.inst_param(status, "status", InstigatorStatus)
        return InstigatorState(
            self.origin,
            instigator_type=self.instigator_type,
            status=status,
            instigator_data=self.instigator_data,
        )

    def with_data(self, instigator_data: InstigatorData) -> "InstigatorState":
        check_instigator_data(self.instigator_type, instigator_data)
        return InstigatorState(
            self.origin,
            instigator_type=self.instigator_type,
            status=self.status,
            instigator_data=instigator_data,
        )

    @property
    def sensor_instigator_data(self) -> Optional["SensorInstigatorData"]:
        if isinstance(self.instigator_data, SensorInstigatorData):
            return self.instigator_data
        return None


@whitelist_for_serdes(old_storage_names={"JobTickStatus"})
class TickStatus(Enum):
    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@whitelist_for_serdes(
    old_storage_names={"JobTick"}, storage_field_names={"tick_data": "job_tick_data"}
)
class InstigatorTick(NamedTuple("_InstigatorTick", [("tick_id", int), ("tick_data", "TickData")])):
    def __new__(cls, tick_id: int, tick_data: "TickData"):
        return super().__new__(
            cls,
            check.int_param(tick_id, "tick_id"),
            check.inst_param(tick_data, "tick_data", TickData),
        )

    def with_status(self, status: TickStatus, **kwargs: Any):
        check.inst_param(status, "status", TickStatus)
        end_timestamp = get_current_timestamp() if status != TickStatus.STARTED else None
        kwargs["end_timestamp"] = end_timestamp
        return self._replace(tick_data=self.tick_data.with_status(status, **kwargs))

    def with_run_requests(
        self, run_requests: Sequence[RunRequest], **kwargs: Any
    ) -> "InstigatorTick":
        return self._replace(tick_data=self.tick_data.with_run_requests(run_requests, **kwargs))

    def with_reason(self, skip_reason: str) -> "InstigatorTick":
        check.opt_str_param(skip_reason, "skip_reason")
        return self._replace(tick_data=self.tick_data.with_reason(skip_reason))

    def with_run_info(self, run_id: Optional[str] = None, run_key: Optional[str] = None):
        return self._replace(tick_data=self.tick_data.with_run_info(run_id, run_key))

    def with_cursor(self, cursor: Optional[str]) -> "InstigatorTick":
        return self._replace(tick_data=self.tick_data.with_cursor(cursor))

    def with_origin_run(self, origin_run_id: str) -> "InstigatorTick":
        return self._replace(tick_data=self.tick_data.with_origin_run(origin_run_id))

    def with_log_key(self, log_key: Sequence[str]) -> "InstigatorTick":
        return self._replace(tick_data=self.tick_data.with_log_key(log_key))

    def with_dynamic_partitions_request_result(
        self,
        dynamic_partitions_request_result: DynamicPartitionsRequestResult,
    ) -> "InstigatorTick":
        return self._replace(
            tick_data=self.tick_data.with_dynamic_partitions_request_result(
                dynamic_partitions_request_result
            )
        )

    def with_user_interrupted(self, user_interrupted: bool) -> "InstigatorTick":
        return self._replace(
            tick_data=self.tick_data.with_user_interrupted(user_interrupted=user_interrupted)
        )

    @property
    def instigator_origin_id(self) -> str:
        return self.tick_data.instigator_origin_id

    @property
    def selector_id(self) -> Optional[str]:
        return self.tick_data.selector_id

    @property
    def instigator_name(self) -> str:
        return self.tick_data.instigator_name

    @property
    def instigator_type(self) -> InstigatorType:
        return self.tick_data.instigator_type

    @property
    def timestamp(self) -> float:
        return self.tick_data.timestamp

    @property
    def end_timestamp(self) -> Optional[float]:
        return self.tick_data.end_timestamp

    @property
    def status(self) -> TickStatus:
        return self.tick_data.status

    @property
    def run_ids(self) -> Sequence[str]:
        return self.tick_data.run_ids

    @property
    def run_keys(self) -> Sequence[str]:
        return self.tick_data.run_keys

    @property
    def error(self) -> Optional[SerializableErrorInfo]:
        return self.tick_data.error

    @property
    def skip_reason(self) -> Optional[str]:
        return self.tick_data.skip_reason

    @property
    def cursor(self) -> Optional[str]:
        return self.tick_data.cursor

    @property
    def origin_run_ids(self) -> Optional[Sequence[str]]:
        return self.tick_data.origin_run_ids

    @property
    def failure_count(self) -> int:
        return self.tick_data.failure_count

    @property
    def log_key(self) -> Optional[list[str]]:
        return self.tick_data.log_key

    @property
    def consecutive_failure_count(self) -> int:
        return self.tick_data.consecutive_failure_count

    @property
    def is_completed(self) -> bool:
        return (
            self.tick_data.status == TickStatus.SUCCESS
            or self.tick_data.status == TickStatus.FAILURE
            or self.tick_data.status == TickStatus.SKIPPED
        )

    @property
    def is_failure(self) -> bool:
        return self.tick_data.status == TickStatus.FAILURE

    @property
    def is_success(self) -> bool:
        return self.tick_data.status == TickStatus.SUCCESS

    @property
    def dynamic_partitions_request_results(
        self,
    ) -> Sequence[DynamicPartitionsRequestResult]:
        return self.tick_data.dynamic_partitions_request_results

    @property
    def requested_asset_materialization_count(self) -> int:
        if self.tick_data.status != TickStatus.SUCCESS:
            return 0

        asset_partitions_from_single_runs = set()
        num_assets_requested_from_backfill_runs = 0
        num_requested_checks = 0
        for run_request in self.tick_data.run_requests or []:
            if run_request.requires_backfill_daemon():
                asset_graph_subset = check.not_none(run_request.asset_graph_subset)
                num_assets_requested_from_backfill_runs += (
                    asset_graph_subset.num_partitions_and_non_partitioned_assets
                )
            else:
                for asset_key in run_request.asset_selection or []:
                    asset_partitions_from_single_runs.add(
                        AssetKeyPartitionKey(asset_key, run_request.partition_key)
                    )
                for asset_check_key in run_request.asset_check_keys or []:
                    num_requested_checks += 1
        return (
            len(asset_partitions_from_single_runs)
            + num_assets_requested_from_backfill_runs
            + num_requested_checks
        )

    @property
    def requested_assets_and_partitions(self) -> Mapping[AssetKey, AbstractSet[str]]:
        if self.tick_data.status != TickStatus.SUCCESS:
            return {}

        partitions_by_asset_key = {}
        for run_request in self.tick_data.run_requests or []:
            if run_request.requires_backfill_daemon():
                asset_graph_subset = check.not_none(run_request.asset_graph_subset)
                for asset_key_partition_key in asset_graph_subset.iterate_asset_partitions():
                    if asset_key_partition_key.asset_key not in partitions_by_asset_key:
                        partitions_by_asset_key[asset_key_partition_key.asset_key] = set()
                    if asset_key_partition_key.partition_key:
                        partitions_by_asset_key[asset_key_partition_key.asset_key].add(
                            asset_key_partition_key.partition_key
                        )
            else:
                for asset_key in run_request.asset_selection or []:
                    if asset_key not in partitions_by_asset_key:
                        partitions_by_asset_key[asset_key] = set()

                    if run_request.partition_key:
                        partitions_by_asset_key[asset_key].add(run_request.partition_key)
                for asset_check_key in run_request.asset_check_keys or []:
                    asset_key = asset_check_key.asset_key
                    if asset_key not in partitions_by_asset_key:
                        partitions_by_asset_key[asset_key] = set()

                    partitions_by_asset_key[asset_key].add(asset_check_key.name)

        return partitions_by_asset_key

    @property
    def requested_asset_keys(self) -> AbstractSet[AssetKey]:
        if self.tick_data.status != TickStatus.SUCCESS:
            return set()

        return set(self.requested_assets_and_partitions.keys())

    @property
    def run_requests(self) -> Optional[Sequence[RunRequest]]:
        return self.tick_data.run_requests

    @property
    def reserved_run_ids_with_requests(self) -> Iterable[tuple[str, RunRequest]]:
        reserved_run_ids = self.tick_data.reserved_run_ids or []
        return zip(reserved_run_ids, self.run_requests or [])

    @property
    def unsubmitted_run_ids_with_requests(self) -> Sequence[tuple[str, RunRequest]]:
        reserved_run_ids = self.tick_data.reserved_run_ids or []
        unrequested_run_ids = set(reserved_run_ids) - set(self.tick_data.run_ids)
        return [
            (run_id, run_request)
            for run_id, run_request in self.reserved_run_ids_with_requests
            if run_id in unrequested_run_ids
        ]

    @property
    def automation_condition_evaluation_id(self) -> int:
        """Returns a unique identifier for the current automation condition evaluation. In general,
        this will be identical to the current tick id, but in cases where an evaluation needs to
        be retried, an override value may be set.
        """
        if self.tick_data.auto_materialize_evaluation_id is not None:
            return self.tick_data.auto_materialize_evaluation_id
        else:
            return self.tick_id


@whitelist_for_serdes(
    old_storage_names={"JobTickData"},
    storage_field_names={
        "instigator_origin_id": "job_origin_id",
        "instigator_name": "job_name",
        "instigator_type": "job_type",
    },
)
class TickData(
    NamedTuple(
        "_TickData",
        [
            ("instigator_origin_id", str),
            ("instigator_name", str),
            ("instigator_type", InstigatorType),
            ("status", TickStatus),
            ("timestamp", float),  # Time the tick started
            ("run_ids", Sequence[str]),
            ("run_keys", Sequence[str]),
            ("error", Optional[SerializableErrorInfo]),
            ("skip_reason", Optional[str]),
            ("cursor", Optional[str]),
            ("origin_run_ids", Sequence[str]),
            ("failure_count", int),
            ("selector_id", Optional[str]),
            ("log_key", Optional[list[str]]),
            (
                "dynamic_partitions_request_results",
                Sequence[DynamicPartitionsRequestResult],
            ),
            ("end_timestamp", Optional[float]),  # Time the tick finished
            ("run_requests", Optional[Sequence[RunRequest]]),  # run requests created by the tick
            ("auto_materialize_evaluation_id", Optional[int]),
            ("reserved_run_ids", Optional[Sequence[str]]),
            ("consecutive_failure_count", int),
            (
                "user_interrupted",
                bool,
            ),  # indicates if a user stopped the tick while submitting runs
        ],
    )
):
    """This class defines the data that is serialized and stored for each schedule/sensor tick. We
    depend on the storage implementation to provide tick ids, and therefore separate all other
    data into this serializable class that can be stored independently of the id.

    Args:
        instigator_origin_id (str): The id of the instigator target for this tick
        instigator_name (str): The name of the instigator for this tick
        instigator_type (InstigatorType): The type of this instigator for this tick
        status (TickStatus): The status of the tick, which can be updated
        timestamp (float): The timestamp at which this instigator evaluation started
        run_id (str): The run created by the tick.
        run_keys (Sequence[str]): Unique user-specified identifiers for the runs created by this
            instigator.
        error (SerializableErrorInfo): The error caught during execution. This is set only when
            the status is ``TickStatus.Failure``
        skip_reason (str): message for why the tick was skipped
        cursor (Optional[str]): Cursor output by this tick.
        origin_run_ids (List[str]): The runs originated from the schedule/sensor.
        failure_count (int): The number of times this particular tick has failed (to determine
            whether the next tick should be a retry of that tick).
            For example, for a schedule, this tracks the number of attempts we have made for a
            particular scheduled execution time. The next tick will attempt to retry the most recent
            tick if it failed and its failure count is less than the configured retry limit.
        dynamic_partitions_request_results (Sequence[DynamicPartitionsRequestResult]): The results
            of the dynamic partitions requests evaluated within the tick.
        end_timestamp (Optional[float]) Time that this tick finished.
        run_requests (Optional[Sequence[RunRequest]]) The RunRequests that were requested by this
            tick. Currently only used by the AUTO_MATERIALIZE type.
        auto_materialize_evaluation_id (Optinoal[int]) For AUTO_MATERIALIZE ticks, the evaluation ID
            that can be used to index into the asset_daemon_asset_evaluations table.
        reserved_run_ids (Optional[Sequence[str]]): A list of run IDs to use for each of the
            run_requests. Used to ensure that if the tick fails partway through, we don't create
            any duplicate runs for the tick. Currently only used by AUTO_MATERIALIZE ticks.
        consecutive_failure_count (Optional[int]): The number of times this instigator has failed
            consecutively. Differs from failure_count in that it spans multiple executions, whereas
            failure_count measures the number of times that a particular tick should retry. For
            example, if a daily schedule fails on 3 consecutive days, failure_count tracks the
            number of failures for each day, and consecutive_failure_count tracks the total
            number of consecutive failures across all days.
    """

    def __new__(
        cls,
        instigator_origin_id: str,
        instigator_name: str,
        instigator_type: InstigatorType,
        status: TickStatus,
        timestamp: float,
        run_ids: Optional[Sequence[str]] = None,
        run_keys: Optional[Sequence[str]] = None,
        error: Optional[SerializableErrorInfo] = None,
        skip_reason: Optional[str] = None,
        cursor: Optional[str] = None,
        origin_run_ids: Optional[Sequence[str]] = None,
        failure_count: Optional[int] = None,
        selector_id: Optional[str] = None,
        log_key: Optional[list[str]] = None,
        dynamic_partitions_request_results: Optional[
            Sequence[DynamicPartitionsRequestResult]
        ] = None,
        end_timestamp: Optional[float] = None,
        run_requests: Optional[Sequence[RunRequest]] = None,
        auto_materialize_evaluation_id: Optional[int] = None,
        reserved_run_ids: Optional[Sequence[str]] = None,
        consecutive_failure_count: Optional[int] = None,
        user_interrupted: bool = False,
    ):
        _validate_tick_args(instigator_type, status, run_ids, error, skip_reason)
        check.opt_list_param(log_key, "log_key", of_type=str)
        return super().__new__(
            cls,
            check.str_param(instigator_origin_id, "instigator_origin_id"),
            check.str_param(instigator_name, "instigator_name"),
            check.inst_param(instigator_type, "instigator_type", InstigatorType),
            check.inst_param(status, "status", TickStatus),
            check.float_param(timestamp, "timestamp"),
            check.opt_sequence_param(run_ids, "run_ids", of_type=str),
            check.opt_sequence_param(run_keys, "run_keys", of_type=str),
            error,  # validated in _validate_tick_args
            skip_reason,  # validated in _validate_tick_args
            cursor=check.opt_str_param(cursor, "cursor"),
            origin_run_ids=check.opt_sequence_param(origin_run_ids, "origin_run_ids", of_type=str),
            failure_count=check.opt_int_param(failure_count, "failure_count", 0),
            selector_id=check.opt_str_param(selector_id, "selector_id"),
            log_key=log_key,
            dynamic_partitions_request_results=check.opt_sequence_param(
                dynamic_partitions_request_results,
                "dynamic_partitions_request_results",
                of_type=DynamicPartitionsRequestResult,
            ),
            end_timestamp=end_timestamp,
            run_requests=check.opt_sequence_param(run_requests, "run_requests"),
            auto_materialize_evaluation_id=auto_materialize_evaluation_id,
            reserved_run_ids=check.opt_sequence_param(reserved_run_ids, "reserved_run_ids"),
            consecutive_failure_count=check.opt_int_param(
                consecutive_failure_count, "consecutive_failure_count", 0
            ),
            user_interrupted=user_interrupted,
        )

    def with_status(
        self,
        status: TickStatus,
        **kwargs,
    ) -> "TickData":
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "status": status,
                },
                kwargs,
            )
        )

    def with_run_info(
        self, run_id: Optional[str] = None, run_key: Optional[str] = None
    ) -> "TickData":
        check.opt_str_param(run_id, "run_id")
        check.opt_str_param(run_key, "run_key")
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "run_ids": (
                        [*self.run_ids, run_id]
                        if (run_id and run_id not in self.run_ids)
                        else self.run_ids
                    ),
                    "run_keys": (
                        [*self.run_keys, run_key]
                        if (run_key and run_key not in self.run_keys)
                        else self.run_keys
                    ),
                },
            )
        )

    def with_run_requests(
        self,
        run_requests: Sequence[RunRequest],
        reserved_run_ids: Optional[Sequence[str]] = None,
        cursor: Optional[str] = None,
    ) -> "TickData":
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "run_requests": run_requests,
                    "reserved_run_ids": reserved_run_ids,
                    "cursor": cursor,
                },
            )
        )

    def with_reason(self, skip_reason: Optional[str]) -> "TickData":
        return TickData(
            **merge_dicts(
                self._asdict(), {"skip_reason": check.opt_str_param(skip_reason, "skip_reason")}
            )
        )

    def with_cursor(self, cursor: Optional[str]) -> "TickData":
        return TickData(
            **merge_dicts(self._asdict(), {"cursor": check.opt_str_param(cursor, "cursor")})
        )

    def with_origin_run(self, origin_run_id: str) -> "TickData":
        check.str_param(origin_run_id, "origin_run_id")
        return TickData(
            **merge_dicts(
                self._asdict(),
                {"origin_run_ids": [*self.origin_run_ids, origin_run_id]},
            )
        )

    def with_log_key(self, log_key: Sequence[str]) -> "TickData":
        return TickData(
            **merge_dicts(
                self._asdict(),
                {"log_key": check.list_param(log_key, "log_key", of_type=str)},
            )
        )

    def with_dynamic_partitions_request_result(
        self, dynamic_partitions_request_result: DynamicPartitionsRequestResult
    ):
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "dynamic_partitions_request_results": [
                        *self.dynamic_partitions_request_results,
                        dynamic_partitions_request_result,
                    ]
                },
            )
        )

    def with_user_interrupted(self, user_interrupted: bool):
        return TickData(
            **merge_dicts(
                self._asdict(),
                {"user_interrupted": user_interrupted},
            )
        )


def _validate_tick_args(
    instigator_type: InstigatorType,
    status: TickStatus,
    run_ids: Optional[Sequence[str]] = None,
    error: Optional[SerializableErrorInfo] = None,
    skip_reason: Optional[str] = None,
) -> None:
    check.inst_param(instigator_type, "instigator_type", InstigatorType)
    check.inst_param(status, "status", TickStatus)

    if status == TickStatus.SUCCESS:
        check.list_param(run_ids, "run_ids", of_type=str)
        check.invariant(error is None, desc="Tick status is SUCCESS, but error was provided")
    elif status == TickStatus.FAILURE:
        check.inst_param(error, "error", SerializableErrorInfo)
    else:
        check.invariant(error is None, "Tick status was not FAILURE but error was provided")

    if skip_reason:
        check.invariant(
            status == TickStatus.SKIPPED,
            "Tick status was not SKIPPED but skip_reason was provided",
        )


@dataclass
class AutoMaterializeAssetEvaluationRecord(Generic[T_EntityKey]):
    id: int
    serialized_evaluation_body: str
    evaluation_id: int
    timestamp: float
    key: T_EntityKey

    @classmethod
    def from_db_row(cls, row) -> "AutoMaterializeAssetEvaluationRecord":
        return AutoMaterializeAssetEvaluationRecord(
            id=row["id"],
            serialized_evaluation_body=row["asset_evaluation_body"],
            evaluation_id=row["evaluation_id"],
            timestamp=utc_datetime_from_naive(row["create_timestamp"]).timestamp(),
            key=entity_key_from_db_string(row["asset_key"]),
        )

    def get_evaluation_with_run_ids(self) -> AutomationConditionEvaluationWithRunIds[T_EntityKey]:
        return deserialize_value(
            self.serialized_evaluation_body, AutomationConditionEvaluationWithRunIds
        )
