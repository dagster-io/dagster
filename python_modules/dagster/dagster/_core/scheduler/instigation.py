from enum import Enum
from inspect import Parameter
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Type, Union

import dagster._check as check
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.host_representation.origin import ExternalInstigatorOrigin
from dagster._core.host_representation.selector import InstigatorSelector, RepositorySelector
from dagster._serdes import create_snapshot_id
from dagster._serdes.serdes import (
    DefaultNamedTupleSerializer,
    WhitelistMap,
    register_serdes_enum_fallbacks,
    register_serdes_tuple_fallbacks,
    replace_storage_keys,
    unpack_inner_value,
    whitelist_for_serdes,
)
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.merger import merge_dicts


@whitelist_for_serdes
class InstigatorStatus(Enum):
    # User has taken some action to start the run instigator
    RUNNING = "RUNNING"

    # The run instigator is running, but only because of its default setting
    AUTOMATICALLY_RUNNING = "AUTOMATICALLY_RUNNING"

    STOPPED = "STOPPED"


register_serdes_enum_fallbacks({"JobStatus": InstigatorStatus})
# for internal backcompat
JobStatus = InstigatorStatus


@whitelist_for_serdes
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


register_serdes_tuple_fallbacks({"SensorJobData": SensorInstigatorData})
# for internal backcompat
SensorJobData = SensorInstigatorData


@whitelist_for_serdes
class ScheduleInstigatorData(
    NamedTuple(
        "_ScheduleInstigatorData",
        [("cron_schedule", Union[str, Sequence[str]]), ("start_timestamp", Optional[float])],
    )
):
    # removed scheduler, 1/5/2022 (0.13.13)
    def __new__(
        cls, cron_schedule: Union[str, Sequence[str]], start_timestamp: Optional[float] = None
    ):
        cron_schedule = check.inst_param(cron_schedule, "cron_schedule", (str, Sequence))
        if not isinstance(cron_schedule, str):
            cron_schedule = check.sequence_param(cron_schedule, "cron_schedule", of_type=str)

        return super(ScheduleInstigatorData, cls).__new__(
            cls,
            cron_schedule,
            # Time in UTC at which the user started running the schedule (distinct from
            # `start_date` on partition-based schedules, which is used to define
            # the range of partitions)
            check.opt_float_param(start_timestamp, "start_timestamp"),
        )


register_serdes_tuple_fallbacks({"ScheduleJobData": ScheduleInstigatorData})
# for internal backcompat
ScheduleJobData = ScheduleInstigatorData


def check_instigator_data(
    instigator_type: InstigatorType,
    instigator_data: Optional[Union[ScheduleInstigatorData, SensorInstigatorData]],
):
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


class InstigatorStateSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type,
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> NamedTuple:
        klass_kwargs = {}
        for key, value in storage_dict.items():
            unpacked = unpack_inner_value(value, whitelist_map, f"{descent_path}.{key}")
            if key in args_for_class:
                klass_kwargs[key] = unpacked
            elif key == "job_type":
                # For backcompat, we store instigator_type as job_type
                klass_kwargs["instigator_type"] = unpacked
            elif key == "job_specific_data":
                # For backcompat, we store instigator_data as job_specific_data
                klass_kwargs["instigator_data"] = unpacked

        return klass(**klass_kwargs)

    @classmethod
    def value_to_storage_dict(
        cls,
        value: NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, Any]:
        storage = super().value_to_storage_dict(
            value,
            whitelist_map,
            descent_path,
        )
        # For backcompat, we store:
        # instigator_type as job_type
        # instigator_data as job_specific_data
        return replace_storage_keys(
            storage,
            {
                "instigator_type": "job_type",
                "instigator_data": "job_specific_data",
            },
        )


@whitelist_for_serdes(serializer=InstigatorStateSerializer)
class InstigatorState(
    NamedTuple(
        "_InstigationState",
        [
            ("origin", ExternalInstigatorOrigin),
            ("instigator_type", InstigatorType),
            ("status", InstigatorStatus),
            ("instigator_data", Optional[Union[ScheduleInstigatorData, SensorInstigatorData]]),
        ],
    )
):
    def __new__(
        cls,
        origin: ExternalInstigatorOrigin,
        instigator_type: InstigatorType,
        status: InstigatorStatus,
        instigator_data: Optional[Union[ScheduleInstigatorData, SensorInstigatorData]] = None,
    ):
        return super(InstigatorState, cls).__new__(
            cls,
            check.inst_param(origin, "origin", ExternalInstigatorOrigin),
            check.inst_param(instigator_type, "instigator_type", InstigatorType),
            check.inst_param(status, "status", InstigatorStatus),
            check_instigator_data(instigator_type, instigator_data),
        )

    @property
    def is_running(self):
        return self.status != InstigatorStatus.STOPPED

    @property
    def name(self):
        return self.origin.instigator_name

    @property
    def instigator_name(self):
        return self.origin.instigator_name

    @property
    def repository_origin_id(self):
        return self.origin.external_repository_origin.get_id()

    @property
    def repository_selector(self) -> RepositorySelector:
        return RepositorySelector(
            self.origin.external_repository_origin.repository_location_origin.location_name,
            self.origin.external_repository_origin.repository_name,
        )

    @property
    def repository_selector_id(self):
        return create_snapshot_id(self.repository_selector)

    @property
    def instigator_origin_id(self):
        return self.origin.get_id()

    @property
    def selector_id(self):
        return create_snapshot_id(
            InstigatorSelector(
                self.origin.external_repository_origin.repository_location_origin.location_name,
                self.origin.external_repository_origin.repository_name,
                self.origin.instigator_name,
            )
        )

    def with_status(self, status):
        check.inst_param(status, "status", InstigatorStatus)
        return InstigatorState(
            self.origin,
            instigator_type=self.instigator_type,
            status=status,
            instigator_data=self.instigator_data,
        )

    def with_data(self, instigator_data):
        check_instigator_data(self.instigator_type, instigator_data)
        return InstigatorState(
            self.origin,
            instigator_type=self.instigator_type,
            status=self.status,
            instigator_data=instigator_data,
        )


register_serdes_tuple_fallbacks({"JobState": InstigatorState})
# for internal backcompat
JobState = InstigatorState


@whitelist_for_serdes
class TickStatus(Enum):
    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


register_serdes_enum_fallbacks({"JobTickStatus": TickStatus})
# for internal backcompat
JobTickStatus = TickStatus


class TickSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type,
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> NamedTuple:
        klass_kwargs = {}
        for key, value in storage_dict.items():
            unpacked = unpack_inner_value(value, whitelist_map, f"{descent_path}.{key}")
            if key in args_for_class:
                klass_kwargs[key] = unpacked
            elif key == "job_tick_data":
                # For backcompat, we store tick_data as job_tick_data
                klass_kwargs["tick_data"] = unpacked

        return klass(**klass_kwargs)

    @classmethod
    def value_to_storage_dict(
        cls,
        value: NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, Any]:
        storage = super().value_to_storage_dict(
            value,
            whitelist_map,
            descent_path,
        )
        # For backcompat, we store:
        # tick_data as job_tick_data
        return replace_storage_keys(
            storage,
            {
                "tick_data": "job_tick_data",
            },
        )


@whitelist_for_serdes(serializer=TickSerializer)
class InstigatorTick(NamedTuple("_InstigatorTick", [("tick_id", int), ("tick_data", "TickData")])):
    def __new__(cls, tick_id: int, tick_data: "TickData"):
        return super(InstigatorTick, cls).__new__(
            cls,
            check.int_param(tick_id, "tick_id"),
            check.inst_param(tick_data, "tick_data", TickData),
        )

    def with_status(self, status, **kwargs):
        check.inst_param(status, "status", TickStatus)
        return self._replace(tick_data=self.tick_data.with_status(status, **kwargs))

    def with_reason(self, skip_reason):
        check.opt_str_param(skip_reason, "skip_reason")
        return self._replace(tick_data=self.tick_data.with_reason(skip_reason))

    def with_run_info(self, run_id=None, run_key=None):
        return self._replace(tick_data=self.tick_data.with_run_info(run_id, run_key))

    def with_cursor(self, cursor):
        return self._replace(tick_data=self.tick_data.with_cursor(cursor))

    def with_origin_run(self, origin_run_id):
        return self._replace(tick_data=self.tick_data.with_origin_run(origin_run_id))

    def with_log_key(self, log_key):
        return self._replace(tick_data=self.tick_data.with_log_key(log_key))

    @property
    def instigator_origin_id(self):
        return self.tick_data.instigator_origin_id

    @property
    def selector_id(self):
        return self.tick_data.selector_id

    @property
    def instigator_name(self):
        return self.tick_data.instigator_name

    @property
    def instigator_type(self):
        return self.tick_data.instigator_type

    @property
    def timestamp(self):
        return self.tick_data.timestamp

    @property
    def status(self):
        return self.tick_data.status

    @property
    def run_ids(self):
        return self.tick_data.run_ids

    @property
    def run_keys(self):
        return self.tick_data.run_keys

    @property
    def error(self):
        return self.tick_data.error

    @property
    def skip_reason(self):
        return self.tick_data.skip_reason

    @property
    def cursor(self):
        return self.tick_data.cursor

    @property
    def origin_run_ids(self):
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


register_serdes_tuple_fallbacks({"JobTick": InstigatorTick})
# for internal backcompat
JobTick = InstigatorTick


class TickDataSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type,
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> NamedTuple:
        klass_kwargs = {}
        for key, value in storage_dict.items():
            unpacked = unpack_inner_value(value, whitelist_map, f"{descent_path}.{key}")
            if key in args_for_class:
                klass_kwargs[key] = unpacked
            elif key == "job_origin_id":
                # For backcompat, we store instigator_origin_id as job_origin_id
                klass_kwargs["instigator_origin_id"] = unpacked
            elif key == "job_name":
                # For backcompat, we store instigator_name as job_name
                klass_kwargs["instigator_name"] = unpacked
            elif key == "job_type":
                # For backcompat, we store instigator_type as job_type
                klass_kwargs["instigator_type"] = unpacked

        return klass(**klass_kwargs)

    @classmethod
    def value_to_storage_dict(
        cls,
        value: NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, Any]:
        storage = super().value_to_storage_dict(
            value,
            whitelist_map,
            descent_path,
        )
        return replace_storage_keys(
            storage,
            {
                "instigator_origin_id": "job_origin_id",
                "instigator_name": "job_name",
                "instigator_type": "job_type",
            },
        )


@whitelist_for_serdes(serializer=TickDataSerializer)
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
        ],
    )
):
    """
    This class defines the data that is serialized and stored for each schedule/sensor tick. We
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
        )

    def with_status(self, status, error=None, timestamp=None, failure_count=None):
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

    def with_run_info(self, run_id=None, run_key=None):
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

    def with_failure_count(self, failure_count):
        return TickData(
            **merge_dicts(
                self._asdict(),
                {
                    "failure_count": failure_count,
                },
            )
        )

    def with_reason(self, skip_reason):
        return TickData(
            **merge_dicts(
                self._asdict(), {"skip_reason": check.opt_str_param(skip_reason, "skip_reason")}
            )
        )

    def with_cursor(self, cursor):
        return TickData(
            **merge_dicts(self._asdict(), {"cursor": check.opt_str_param(cursor, "cursor")})
        )

    def with_origin_run(self, origin_run_id):
        check.str_param(origin_run_id, "origin_run_id")
        return TickData(
            **merge_dicts(
                self._asdict(),
                {"origin_run_ids": [*self.origin_run_ids, origin_run_id]},
            )
        )

    def with_log_key(self, log_key):
        return TickData(
            **merge_dicts(
                self._asdict(),
                {"log_key": check.list_param(log_key, "log_key", of_type=str)},
            )
        )


register_serdes_tuple_fallbacks({"JobTickData": TickData})
# for internal backcompat
JobTickData = TickData


def _validate_tick_args(instigator_type, status, run_ids=None, error=None, skip_reason=None):
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
