import datetime
from typing import Callable, Iterator, Optional, Sequence, Tuple, Union, cast

import pendulum

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.decorators.asset_check_decorator import (
    asset_check,
)
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import (
    AssetCheckExecutionContext,
)
from dagster._core.instance import DagsterInstance
from dagster._utils.schedules import get_latest_completed_cron_tick, is_valid_cron_string

from ..assets import AssetsDefinition, SourceAsset
from ..events import AssetKey, CoercibleToAssetKey

DEFAULT_FRESHNESS_SEVERITY = AssetCheckSeverity.WARN
DEFAULT_UPPER_BOUND_CRON_TIMEZONE = "UTC"
TIME_WINDOW_SIZE_METADATA_KEY = "dagster/time_window_size"
UPPER_BOUND_CRON_METADATA_KEY = "dagster/upper_bound_cron"
UPPER_BOUND_CRON_TIMEZONE_METADATA_KEY = "dagster/upper_bound_cron_timezone"
LAST_UPDATED_TIMESTAMP_METADATA_KEY = "dagster/last_updated_timestamp"
FRESHNESS_PARAMS_METADATA_KEY = "dagster/freshness_params"


def ensure_no_duplicate_assets(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
) -> None:
    """Finds duplicate assets in the provided list of assets, and errors if any are present.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]): The assets to check for duplicates.

    Returns:
        Sequence[AssetKey]: A list of the duplicate assets.
    """
    asset_keys = [
        asset_key for asset in assets for asset_key in list(asset_to_keys_iterable(asset))
    ]
    duplicate_assets = [asset_key for asset_key in asset_keys if asset_keys.count(asset_key) > 1]
    check.invariant(
        len(duplicate_assets) == 0,
        f"Found duplicate assets in the provided list of assets: {duplicate_assets}. Please ensure that each asset is unique.",
    )


def asset_to_keys_iterable(
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
) -> Iterator[AssetKey]:
    """Converts the provided asset construct to a sequence of AssetKeys.

    Args:
        asset (Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The asset to convert to a sequence of AssetKeys.

    Returns:
        Sequence[AssetKey]: A sequence of AssetKeys.
    """
    if isinstance(asset, AssetsDefinition):
        yield from asset.keys
    elif isinstance(asset, SourceAsset):
        yield asset.key
    else:
        yield AssetKey.from_coercible_or_definition(asset)


def ensure_no_duplicate_asset_checks(
    asset_checks: Sequence[AssetChecksDefinition],
) -> None:
    asset_check_keys = [
        asset_check_key
        for asset_check in asset_checks
        for asset_check_key in asset_check.check_keys
    ]
    duplicate_asset_checks = [
        asset_check_key
        for asset_check_key in asset_check_keys
        if asset_check_keys.count(asset_check_key) > 1
    ]
    check.invariant(
        len(duplicate_asset_checks) == 0,
        f"Found duplicate asset checks in the provided list of asset checks: {duplicate_asset_checks}. Please ensure that each provided asset check is unique.",
    )


def retrieve_latest_record(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partition_key: Optional[str],
) -> Optional[EventLogRecord]:
    """Retrieve the latest materialization or observation record for the given asset.

    If the asset is partitioned, the latest record for the latest partition will be returned.
    """
    materializations = instance.fetch_materializations(
        records_filter=AssetRecordsFilter(
            asset_key=asset_key, asset_partitions=[partition_key] if partition_key else None
        ),
        limit=1,
    )
    observations = instance.fetch_observations(
        records_filter=AssetRecordsFilter(
            asset_key=asset_key, asset_partitions=[partition_key] if partition_key else None
        ),
        limit=1,
    )
    if materializations.records and observations.records:
        return max(
            materializations.records[0],
            observations.records[0],
            key=lambda record: retrieve_timestamp_from_record(record),
        )
    else:
        return (
            materializations.records[0]
            if materializations.records
            else observations.records[0]
            if observations.records
            else None
        )


def retrieve_timestamp_from_record(asset_record: EventLogRecord) -> float:
    """Retrieve the timestamp from the given materialization or observation record."""
    check.inst_param(asset_record, "asset_record", EventLogRecord)
    if asset_record.event_log_entry.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION:
        return asset_record.timestamp
    else:
        metadata = check.not_none(asset_record.asset_observation).metadata
        value = metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY].value
        check.invariant(
            isinstance(value, float),
            f"Unexpected metadata value type for '{LAST_UPDATED_TIMESTAMP_METADATA_KEY}': "
            f"{type(metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY])}",
        )
        return cast(float, value)


def get_arrival_timestamp(record: Optional[EventLogRecord]) -> Optional[float]:
    if record is None:
        return None
    if record.asset_materialization is not None:
        return record.timestamp
    elif record.asset_observation is not None:
        metadata_value = record.asset_observation.metadata.get("dagster/last_updated_timestamp")
        if metadata_value is not None:
            return check.float_param(metadata_value.value, "last_updated_timestamp")
        else:
            return None
    else:
        check.failed("Expected record to be an observation or materialization")


def ensure_freshness_checks(checks: Sequence[AssetChecksDefinition]) -> None:
    for check_def in checks:
        for check_spec in check_def.check_specs:
            check.invariant(
                check_spec.metadata and check_spec.metadata.get(FRESHNESS_PARAMS_METADATA_KEY),
                f"Asset check {check_spec.key} didn't have expected metadata. Please ensure that the asset check is a freshness check.",
            )


def get_time_window(
    upper_bound_cron: Optional[str],
    current_timestamp: float,
    upper_bound_cron_timezone: str,
    time_window_size: Optional[datetime.timedelta],
) -> Tuple[Optional[datetime.datetime], datetime.datetime]:
    """Get the time window we expect the asset to arrive in given the provided parameters, as well
    as the most recently completed partition key.
    """
    current_time_in_freshness_tz = pendulum.from_timestamp(
        current_timestamp, tz=upper_bound_cron_timezone
    )
    # If an upper bound cron is provided, then the upper bound of the time window is the most recent
    # tick of the cron schedule. Otherwise, the upper bound is the current time.
    upper_bound = (
        check.not_none(
            get_latest_completed_cron_tick(
                cron=upper_bound_cron,
                current_time=current_time_in_freshness_tz,
                timezone=upper_bound_cron_timezone,
            )
        )
        if upper_bound_cron
        else current_time_in_freshness_tz
    )
    lower_bound = (
        upper_bound - time_window_size if time_window_size else None
    )  # lower bound is implicitly the start of the latest completed partition
    return lower_bound, upper_bound


def get_latest_completed_partition_key(
    upper_bound_cron: Optional[str],
    current_timestamp: float,
    upper_bound_cron_timezone: str,
    partitions_def: Optional[TimeWindowPartitionsDefinition],
) -> Optional[str]:
    """Get the latest complete partition key for the given cron schedule."""
    if not partitions_def:
        return None
    current_time_in_freshness_tz = pendulum.from_timestamp(
        current_timestamp, tz=upper_bound_cron_timezone
    )
    latest_cron_tick_time = check.not_none(
        get_latest_completed_cron_tick(
            cron=upper_bound_cron,
            current_time=current_time_in_freshness_tz,
            timezone=upper_bound_cron_timezone,
        )
    )
    latest_cron_tick_time_in_partitions_def_tz = pendulum.from_timestamp(
        latest_cron_tick_time.timestamp(), tz=partitions_def.timezone
    )
    time_window = check.not_none(
        partitions_def.get_prev_partition_window(latest_cron_tick_time_in_partitions_def_tz)
    )
    return partitions_def.get_partition_key_range_for_time_window(time_window).start


def build_freshness_check(
    asset_key: AssetKey,
    upper_bound_cron: Optional[str],
    upper_bound_cron_timezone: str,
    severity: AssetCheckSeverity,
    fail_on_late_arrival: bool,
    time_window_size: datetime.timedelta,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]],
) -> AssetChecksDefinition:
    params_metadata = {}
    if upper_bound_cron:
        params_metadata[UPPER_BOUND_CRON_METADATA_KEY] = upper_bound_cron
        params_metadata[UPPER_BOUND_CRON_TIMEZONE_METADATA_KEY] = upper_bound_cron_timezone
    if time_window_size:
        params_metadata[TIME_WINDOW_SIZE_METADATA_KEY] = time_window_size.total_seconds()

    @asset_check(
        asset=asset_key,
        description="Evaluates freshness for targeted asset.",
        name="freshness_check",
        metadata={FRESHNESS_PARAMS_METADATA_KEY: params_metadata},
    )
    def the_check(context: AssetCheckExecutionContext) -> AssetCheckResult:
        if asset_property_enforcement_lambda:
            asset_property_enforcement_lambda(
                context.job_def.asset_layer.asset_graph.get(asset_key).assets_def
            )
        current_timestamp = pendulum.now("UTC").timestamp()

        # Explicit call to partitions def here will be replaced with AssetSlice reference once it's available.
        partitions_def = cast(
            Optional[TimeWindowPartitionsDefinition],
            context.job_def.asset_layer.asset_graph.get(asset_key).partitions_def,
        )
        check.invariant(
            partitions_def is None or isinstance(partitions_def, TimeWindowPartitionsDefinition),
            "Expected partitions_def to be time-windowed.",
        )

        lower_bound, upper_bound = get_time_window(
            upper_bound_cron=upper_bound_cron,
            upper_bound_cron_timezone=upper_bound_cron_timezone,
            current_timestamp=current_timestamp,
            time_window_size=time_window_size,
        )
        expected_partition_key = get_latest_completed_partition_key(
            upper_bound_cron=upper_bound_cron,
            current_timestamp=current_timestamp,
            upper_bound_cron_timezone=upper_bound_cron_timezone,
            partitions_def=partitions_def,
        )
        latest_record = retrieve_latest_record(
            instance=context.instance, asset_key=asset_key, partition_key=expected_partition_key
        )
        arrival_timestamp = get_arrival_timestamp(latest_record)
        lower_bound_timestamp = (
            lower_bound.timestamp() if lower_bound else 0
        )  # Indicating that we expect it to be trivial if not derived
        is_late = arrival_timestamp is not None and arrival_timestamp > upper_bound.timestamp()
        passed = arrival_timestamp is not None and (
            upper_bound.timestamp() >= arrival_timestamp >= lower_bound_timestamp
            if fail_on_late_arrival
            else arrival_timestamp >= lower_bound_timestamp
        )

        return AssetCheckResult(
            passed=passed,
            description=get_description_for_check_result(
                passed,
                arrival_timestamp,
                upper_bound,
                lower_bound,
                is_late,
                current_timestamp,
                expected_partition_key,
            ),
            severity=severity,
        )

    return the_check


def get_description_for_check_result(
    passed: bool,
    arrival_timestamp: Optional[float],
    upper_bound: datetime.datetime,
    lower_bound: Optional[datetime.datetime],
    is_late: bool,
    current_timestamp: float,
    expected_partition_key: Optional[str],
) -> str:
    check.invariant(
        (passed and arrival_timestamp is not None) or not passed,
        "Should not be possible for check to pass without a record.",
    )
    descriptor = f"partition {expected_partition_key}" if expected_partition_key else "asset"
    duration_since_upper_bound = pendulum.duration(
        seconds=current_timestamp - upper_bound.timestamp()
    )
    duration_since_lower_bound = (
        pendulum.duration(seconds=current_timestamp - lower_bound.timestamp())
        if lower_bound
        else None
    )
    expected_by = f"{duration_since_upper_bound.in_words()} ago" + (
        f" (and no earlier than {duration_since_lower_bound.in_words()} ago)"
        if duration_since_lower_bound
        else ""
    )
    arrival_result = (
        f"arrived {pendulum.duration(seconds=current_timestamp - arrival_timestamp).in_words()} ago"
        if arrival_timestamp
        else "has not arrived"
    )

    check_result_implication = (
        "The check passed, since it arrived on time"
        if passed and not is_late
        else "The check passed, since despite it being overdue, the asset has since arrived."
        if passed and is_late
        else "The check failed, since the asset has not arrived."
        if not arrival_timestamp
        else "The check failed, since the asset arrived late."
    )
    return f"The most recent record for the {descriptor} {arrival_result}, and was expected {expected_by}. {check_result_implication}"


def build_freshness_checks_for_assets(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    upper_bound_cron: Optional[str],
    upper_bound_cron_timezone: str,
    severity: AssetCheckSeverity,
    fail_on_late_arrival: bool = False,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]] = None,
    time_window_size: datetime.timedelta = datetime.timedelta(minutes=0),
) -> Sequence[AssetChecksDefinition]:
    ensure_no_duplicate_assets(assets)
    upper_bound_cron = check.opt_str_param(upper_bound_cron, "upper_bound_cron")
    check.invariant(
        is_valid_cron_string(upper_bound_cron) if upper_bound_cron else True,
        "upper_bound_cron must be a valid cron string.",
    )
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)
    upper_bound_cron_timezone = check.str_param(
        upper_bound_cron_timezone, "upper_bound_cron_timezone"
    )
    time_window_size = check.inst_param(time_window_size, "time_window_size", datetime.timedelta)

    return [
        build_freshness_check(
            asset_key=asset_key,
            upper_bound_cron=upper_bound_cron,
            upper_bound_cron_timezone=upper_bound_cron_timezone,
            severity=severity,
            fail_on_late_arrival=fail_on_late_arrival,
            time_window_size=time_window_size,
            asset_property_enforcement_lambda=asset_property_enforcement_lambda,
        )
        for asset in assets
        for asset_key in asset_to_keys_iterable(asset)
    ]
