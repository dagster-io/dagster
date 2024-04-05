import datetime
from typing import Any, Iterator, Mapping, Optional, Sequence

import pendulum
from pydantic import BaseModel

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
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

from ..asset_check_spec import AssetCheckKey, AssetCheckSpec
from ..asset_checks import AssetChecksDefinition
from ..asset_selection import AssetSelection
from ..decorators import sensor
from ..sensor_definition import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext
from .shared_builder import evaluate_freshness_check
from .utils import (
    DEADLINE_CRON_METADATA_KEY,
    DEFAULT_FRESHNESS_TIMEZONE,
    FRESHNESS_PARAMS_METADATA_KEY,
    FRESHNESS_TIMEZONE_METADATA_KEY,
    LOWER_BOUND_DELTA_METADATA_KEY,
    ensure_no_duplicate_asset_checks,
)

DEFAULT_FRESHNESS_SENSOR_NAME = "freshness_checks_sensor"


class CheckEvaluationsSerializer(FieldSerializer):
    def pack(
        self,
        mapping: Mapping[str, AssetCheckResult],
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


@whitelist_for_serdes(field_serializers={"check_evaluations_by_key": CheckEvaluationsSerializer})
class FreshnessCheckSensorCursor(BaseModel):
    """The cursor for the freshness check sensor."""

    check_evaluations_by_key: Mapping[AssetCheckKey, AssetCheckResult]
    last_evaluated_check_key: Optional[AssetCheckKey] = None

    def get_last_check_evaluation(self, key: AssetCheckKey) -> Optional[AssetCheckResult]:
        return self.check_evaluations_by_key.get(key)

    @staticmethod
    def empty():
        return FreshnessCheckSensorCursor(check_evaluations_by_key={})

    def with_updated_evaluation(
        self, key: AssetCheckKey, evaluation: AssetCheckResult
    ) -> "FreshnessCheckSensorCursor":
        return FreshnessCheckSensorCursor(
            check_evaluations_by_key=merge_dicts(self.check_evaluations_by_key, {key: evaluation}),
            last_evaluated_check_key=key,
        )


MAXIMUM_SENSOR_RUNTIME_SECONDS = 40  # Leave some buffer for grpc communication overhead


@experimental
def build_sensor_for_freshness_checks(
    *,
    freshness_checks: Optional[Sequence[AssetChecksDefinition]] = None,
    check_selection: Optional[AssetSelection] = None,
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
        freshness_checks (Optional[Sequence[AssetChecksDefinition]]): The freshness checks to evaluate.
            Either this or check_selection must be provided.
        check_selection (Optional[AssetSelection]): The asset checks to evaluate. The provided
            selection must resolve to a set of freshness checks, will result in an error otherwise.
            Either this or freshness_checks must be provided.
        minimum_interval_seconds (Optional[int]): The duration in seconds between evaluations of the sensor.
        name (Optional[str]): The name of the sensor. Defaults to "freshness_check_sensor", but a
            name may need to be provided in case of multiple calls of this function.
        default_status (Optional[DefaultSensorStatus]): The default status of the sensor. Defaults
            to stopped.

    Returns:
        SensorDefinition: The sensor that evaluates the freshness of the assets.
    """
    check.opt_sequence_param(freshness_checks, "freshness_checks")
    check.opt_inst_param(check_selection, "check_selection", AssetSelection)
    check.invariant(
        freshness_checks is not None or check_selection is not None,
        "Exactly one of freshness_checks or check_selection must be provided.",
    )
    check.invariant(
        freshness_checks is None or check_selection is None,
        "Only one of freshness_checks or check_selection can be provided.",
    )
    if freshness_checks:
        ensure_no_duplicate_asset_checks(freshness_checks)
    check.invariant(
        check.int_param(minimum_interval_seconds, "minimum_interval_seconds") > 0
        if minimum_interval_seconds
        else True,
        "Interval must be a positive integer.",
    )
    check.str_param(name, "name")
    if freshness_checks:
        selection = AssetSelection.checks(*freshness_checks)
    elif check_selection:
        selection = check_selection
    else:
        check.failed("Should not be possible")

    job_name = f"{name}_job"

    @sensor(
        name=name,
        minimum_interval_seconds=minimum_interval_seconds,
        description="Evaluates the freshness of targeted assets.",
        job=define_asset_job(job_name, selection=selection),
        default_status=default_status,
    )
    def the_sensor(context: SensorEvaluationContext) -> Iterator[AssetCheckResult]:
        iteration_start_time = pendulum.now("UTC").timestamp()
        while (
            pendulum.now("UTC").timestamp() - iteration_start_time < MAXIMUM_SENSOR_RUNTIME_SECONDS
        ):
            for result in evaluate_freshness_loop(context, job_name):
                if result:
                    yield result

    return the_sensor


def evaluate_freshness_loop(
    context: SensorEvaluationContext, job_name: str
) -> Iterator[Optional[AssetCheckResult]]:
    cursor = (
        deserialize_value(context.cursor, FreshnessCheckSensorCursor)
        if context.cursor
        else FreshnessCheckSensorCursor.empty()
    )
    job_def = check.not_none(check.not_none(context.repository_def).get_job(job_name))
    for check_key in job_def.asset_layer.assets_defs_by_check_key.keys():
        previous_evaluation = cursor.get_last_check_evaluation(check_key)
        result = evaluate_freshness_check(check_key, job_def, context.instance)
        state_change = previous_evaluation is None or result.passed != previous_evaluation.passed
        cursor = cursor.with_updated_evaluation(check_key, result)
        context.update_cursor(serialize_value(cursor))
        # We only yield new results on state change.
        yield result if state_change else None


def should_run_again(
    check_spec: AssetCheckSpec, prev_evaluation_timestamp: Optional[float], current_timestamp: float
) -> bool:
    metadata = check_spec.metadata
    if not metadata:
        # This should never happen, but type hinting prevents us from using check.not_none
        check.assert_never(metadata)

    if not prev_evaluation_timestamp:
        return True

    timezone = get_freshness_cron_timezone(metadata) or DEFAULT_FRESHNESS_TIMEZONE
    current_time = pendulum.from_timestamp(current_timestamp, tz=timezone)
    prev_evaluation_time = pendulum.from_timestamp(prev_evaluation_timestamp, tz=timezone)

    deadline_cron = get_freshness_cron(metadata)
    if deadline_cron:
        latest_completed_cron_tick = check.not_none(
            get_latest_completed_cron_tick(deadline_cron, current_time, timezone)
        )
        return latest_completed_cron_tick > prev_evaluation_time

    lower_bound_delta = check.not_none(get_lower_bound_delta(metadata))
    return current_time > prev_evaluation_time + lower_bound_delta


def get_metadata(check_spec: AssetCheckSpec) -> Mapping[str, Any]:
    if check_spec.metadata:
        return check_spec.metadata
    check.assert_never(check_spec.metadata)


def get_freshness_cron(metadata: Mapping[str, Any]) -> Optional[str]:
    return metadata[FRESHNESS_PARAMS_METADATA_KEY].get(DEADLINE_CRON_METADATA_KEY)


def get_freshness_cron_timezone(metadata: Mapping[str, Any]) -> Optional[str]:
    return metadata[FRESHNESS_PARAMS_METADATA_KEY].get(FRESHNESS_TIMEZONE_METADATA_KEY)


def get_lower_bound_delta(metadata: Mapping[str, Any]) -> Optional[datetime.timedelta]:
    float_delta: float = metadata[FRESHNESS_PARAMS_METADATA_KEY].get(LOWER_BOUND_DELTA_METADATA_KEY)
    return datetime.timedelta(seconds=float_delta) if float_delta else None
