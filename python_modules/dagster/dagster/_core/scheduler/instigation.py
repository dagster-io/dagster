from enum import Enum
from typing import Any, List, NamedTuple, Optional, Sequence, Union

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.definitions.auto_materialize_condition import AutoMaterializeAssetEvaluation

# re-export
from dagster._core.definitions.run_request import (
    InstigatorType as InstigatorType,
    SkipReason as SkipReason,
)
from dagster._core.definitions.selector import InstigatorSelector, RepositorySelector
from dagster._core.host_representation.origin import ExternalInstigatorOrigin
from dagster._serdes import create_snapshot_id
from dagster._serdes.serdes import (
    deserialize_value,
    whitelist_for_serdes,
)
from dagster._utils import datetime_as_float, xor
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.merger import merge_dicts

InstigatorData: TypeAlias = Union["ScheduleInstigatorData", "SensorInstigatorData"]


@whitelist_for_serdes(old_storage_names={"JobStatus"})
class InstigatorStatus(Enum):
    # User has taken some action to start the run instigator
    RUNNING = "RUNNING"

    # The run instigator is running, but only because of its default setting
    AUTOMATICALLY_RUNNING = "AUTOMATICALLY_RUNNING"

    STOPPED = "STOPPED"


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

        return super(DynamicPartitionsRequestResult, cls).__new__(
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
    ):
        return super(SensorInstigatorData, cls).__new__(
            cls,
            check.opt_float_param(last_tick_timestamp, "last_tick_timestamp"),
            check.opt_str_param(last_run_key, "last_run_key"),
            check.opt_int_param(min_interval, "min_interval"),
            check.opt_str_param(cursor, "cursor"),
            check.opt_float_param(last_tick_start_timestamp, "last_tick_start_timestamp"),
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

        return super(ScheduleInstigatorData, cls).__new__(
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
            ("origin", ExternalInstigatorOrigin),
            ("instigator_type", InstigatorType),
            ("status", InstigatorStatus),
            ("instigator_data", Optional[InstigatorData]),
        ],
    )
):
    def __new__(
        cls,
        origin: ExternalInstigatorOrigin,
        instigator_type: InstigatorType,
        status: InstigatorStatus,
        instigator_data: Optional[InstigatorData] = None,
    ):
        return super(InstigatorState, cls).__new__(
            cls,
            check.inst_param(origin, "origin", ExternalInstigatorOrigin),
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
        return self.origin.external_repository_origin.get_id()

    @property
    def repository_selector(self) -> RepositorySelector:
        return RepositorySelector(
            self.origin.external_repository_origin.code_location_origin.location_name,
            self.origin.external_repository_origin.repository_name,
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
                self.origin.external_repository_origin.code_location_origin.location_name,
                self.origin.external_repository_origin.repository_name,
                self.origin.instigator_name,
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
        return super(InstigatorTick, cls).__new__(
            cls,
            check.int_param(tick_id, "tick_id"),
            check.inst_param(tick_data, "tick_data", TickData),
        )

    def with_status(self, status: TickStatus, **kwargs: Any):
        check.inst_param(status, "status", TickStatus)
        return self._replace(tick_data=self.tick_data.with_status(status, **kwargs))

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
    def log_key(self) -> Optional[List[str]]:
        return self.tick_data.log_key

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
            ("timestamp", float),
            ("run_ids", Sequence[str]),
            ("run_keys", Sequence[str]),
            ("error", Optional[SerializableErrorInfo]),
            ("skip_reason", Optional[str]),
            ("cursor", Optional[str]),
            ("origin_run_ids", Sequence[str]),
            ("failure_count", int),
            ("selector_id", Optional[str]),
            ("log_key", Optional[List[str]]),
            (
                "dynamic_partitions_request_results",
                Sequence[DynamicPartitionsRequestResult],
            ),
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
        error (SerializableErrorInfo): The error caught during execution. This is set only when
            the status is ``TickStatus.Failure``
        skip_reason (str): message for why the tick was skipped
        origin_run_ids (List[str]): The runs originated from the schedule/sensor.
        failure_count (int): The number of times this tick has failed. If the status is not
            FAILED, this is the number of previous failures before it reached the current state.
        dynamic_partitions_request_results (Sequence[DynamicPartitionsRequestResult]): The results
            of the dynamic partitions requests evaluated within the tick.

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
        log_key: Optional[List[str]] = None,
        dynamic_partitions_request_results: Optional[
            Sequence[DynamicPartitionsRequestResult]
        ] = None,
    ):
        _validate_tick_args(instigator_type, status, run_ids, error, skip_reason)
        check.opt_list_param(log_key, "log_key", of_type=str)
        return super(TickData, cls).__new__(
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
        )

    def with_status(
        self,
        status: TickStatus,
        error: Optional[SerializableErrorInfo] = None,
        timestamp: Optional[float] = None,
        failure_count: Optional[int] = None,
    ) -> "TickData":
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "status": status,
                    "error": error,
                    "timestamp": timestamp if timestamp is not None else self.timestamp,
                    "failure_count": (
                        failure_count if failure_count is not None else self.failure_count
                    ),
                },
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

    def with_failure_count(self, failure_count: int) -> "TickData":
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "failure_count": failure_count,
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


class AutoMaterializeAssetEvaluationRecord(NamedTuple):
    id: int
    evaluation: AutoMaterializeAssetEvaluation
    evaluation_id: int
    timestamp: float

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row["id"],
            evaluation=deserialize_value(
                row["asset_evaluation_body"], AutoMaterializeAssetEvaluation
            ),
            evaluation_id=row["evaluation_id"],
            timestamp=datetime_as_float(row["create_timestamp"]),
        )
