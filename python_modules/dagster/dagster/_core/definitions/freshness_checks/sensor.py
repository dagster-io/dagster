from typing import Any, Mapping, Optional, Sequence

import pendulum
from pydantic import BaseModel

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.run_request import RunRequest
from dagster._serdes.serdes import (
    FieldSerializer,
    JsonSerializableValue,
    PackableValue,
    SerializableNonScalarKeyMapping,
    UnpackContext,
    WhitelistMap,
    deserialize_value,
    pack_value,
    serialize_value,
    unpack_value,
    whitelist_for_serdes,
)
from dagster._utils.merger import merge_dicts
from dagster._utils.schedules import get_latest_completed_cron_tick

from ..asset_checks import AssetChecksDefinition
from ..decorators import sensor
from ..sensor_definition import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext
from .non_partitioned import NON_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY
from .time_window_partitioned import TIME_WINDOW_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY
from .utils import (
    DEFAULT_FRESHNESS_CRON_TIMEZONE,
    FRESHNESS_CRON_METADATA_KEY,
    FRESHNESS_CRON_TIMEZONE_METADATA_KEY,
    MAXIMUM_LAG_METADATA_KEY,
    ensure_freshness_checks,
    ensure_no_duplicate_asset_checks,
)

DEFAULT_FRESHNESS_SENSOR_NAME = "freshness_checks_sensor"


class EvaluationTimestampsSerializer(FieldSerializer):
    def pack(
        self,
        mapping: Mapping[str, float],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        return pack_value(SerializableNonScalarKeyMapping(mapping), whitelist_map, descent_path)

    def unpack(
        self,
        unpacked_value: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue:
        return unpack_value(unpacked_value, dict, whitelist_map, context)


@whitelist_for_serdes(
    field_serializers={"evaluation_timestamps_by_check_key": EvaluationTimestampsSerializer}
)
class FreshnessCheckSensorCursor(BaseModel):
    """The cursor for the freshness check sensor."""

    evaluation_timestamps_by_check_key: Mapping[AssetCheckKey, float]

    def get_last_evaluation_timestamp(self, key: AssetCheckKey) -> Optional[float]:
        return self.evaluation_timestamps_by_check_key.get(key)

    @staticmethod
    def empty():
        return FreshnessCheckSensorCursor(evaluation_timestamps_by_check_key={})

    def with_updated_evaluations(
        self, keys: Sequence[AssetCheckKey], evaluation_timestamp: float
    ) -> "FreshnessCheckSensorCursor":
        return FreshnessCheckSensorCursor(
            evaluation_timestamps_by_check_key=merge_dicts(
                self.evaluation_timestamps_by_check_key,
                {key: evaluation_timestamp for key in keys},
            )
        )


@experimental
def build_sensor_for_freshness_checks(
    *,
    freshness_checks: Sequence[AssetChecksDefinition],
    minimum_interval_seconds: Optional[int] = None,
    name: str = DEFAULT_FRESHNESS_SENSOR_NAME,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> SensorDefinition:
    """Builds a sensor which kicks off evaluation of freshness checks.

    The sensor will introspect from the parameters of the passed-in freshness checks how often to
    run them. IE, if the freshness check is based on a cron schedule, the sensor will request one
    run of the check per tick of the cron. If the freshness check is based on a maximum lag, the
    sensor will request one run of the check per interval specified by the maximum lag.

    Args:
        freshness_checks (Sequence[AssetChecksDefinition]): The freshness checks to evaluate.
        minimum_interval_seconds (Optional[int]): The duration in seconds between evaluations of the sensor.
        name (Optional[str]): The name of the sensor. Defaults to "freshness_check_sensor", but a
            name may need to be provided in case of multiple calls of this function.
        default_status (Optional[DefaultSensorStatus]): The default status of the sensor. Defaults
            to stopped.

    Returns:
        SensorDefinition: The sensor that evaluates the freshness of the assets.
    """
    freshness_checks = check.sequence_param(freshness_checks, "freshness_checks")
    ensure_no_duplicate_asset_checks(freshness_checks)
    ensure_freshness_checks(freshness_checks)
    check.invariant(
        check.int_param(minimum_interval_seconds, "minimum_interval_seconds") > 0
        if minimum_interval_seconds
        else True,
        "Interval must be a positive integer.",
    )
    check.str_param(name, "name")

    @sensor(
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        description="Evaluates the freshness of targeted assets.",
        asset_selection=AssetSelection.checks(*freshness_checks),
        default_status=default_status,
    )
    def the_sensor(context: SensorEvaluationContext) -> Optional[RunRequest]:
        cursor = (
            deserialize_value(context.cursor, FreshnessCheckSensorCursor)
            if context.cursor
            else FreshnessCheckSensorCursor.empty()
        )
        current_timestamp = pendulum.now("UTC").timestamp()
        check_keys_to_run = []
        for asset_check in freshness_checks:
            for asset_check_spec in asset_check.check_specs:
                prev_evaluation_timestamp = cursor.get_last_evaluation_timestamp(
                    asset_check_spec.key
                )
                if should_run_again(asset_check_spec, prev_evaluation_timestamp, current_timestamp):
                    check_keys_to_run.append(asset_check_spec.key)
        context.update_cursor(
            serialize_value(cursor.with_updated_evaluations(check_keys_to_run, current_timestamp))
        )
        if check_keys_to_run:
            return RunRequest(asset_check_keys=check_keys_to_run)

    return the_sensor


def should_run_again(
    check_spec: AssetCheckSpec, prev_evaluation_timestamp: Optional[float], current_timestamp: float
) -> bool:
    metadata = check_spec.metadata
    if not metadata:
        # This should never happen, but type hinting prevents us from using check.not_none
        check.assert_never(metadata)

    if not prev_evaluation_timestamp:
        return True

    timezone = get_freshness_cron_timezone(metadata) or DEFAULT_FRESHNESS_CRON_TIMEZONE
    current_time = pendulum.from_timestamp(current_timestamp, tz=timezone)
    prev_evaluation_time = pendulum.from_timestamp(prev_evaluation_timestamp, tz=timezone)

    freshness_cron = get_freshness_cron(metadata)
    if freshness_cron:
        latest_completed_cron_tick = check.not_none(
            get_latest_completed_cron_tick(freshness_cron, current_time, timezone)
        )
        return latest_completed_cron_tick > prev_evaluation_time

    maximum_lag_minutes = check.not_none(get_maximum_lag_minutes(metadata))
    return current_time > prev_evaluation_time.add(minutes=maximum_lag_minutes)


def get_metadata(check_spec: AssetCheckSpec) -> Mapping[str, Any]:
    if check_spec.metadata:
        return check_spec.metadata
    check.assert_never(check_spec.metadata)


def get_params_key(metadata: Mapping[str, Any]) -> str:
    return (
        TIME_WINDOW_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY
        if TIME_WINDOW_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY in metadata
        else NON_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY
    )


def get_freshness_cron(metadata: Mapping[str, Any]) -> Optional[str]:
    return metadata[get_params_key(metadata)].get(FRESHNESS_CRON_METADATA_KEY)


def get_freshness_cron_timezone(metadata: Mapping[str, Any]) -> Optional[str]:
    return metadata[get_params_key(metadata)].get(FRESHNESS_CRON_TIMEZONE_METADATA_KEY)


def get_maximum_lag_minutes(metadata: Mapping[str, Any]) -> int:
    return metadata[NON_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY].get(MAXIMUM_LAG_METADATA_KEY)
