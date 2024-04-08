import datetime
import hashlib
from typing import Callable, Iterable, Iterator, Optional, Sequence, Union, cast

import pendulum

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity, AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.decorators.asset_check_decorator import (
    multi_asset_check,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
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
DEFAULT_FRESHNESS_TIMEZONE = "UTC"
LOWER_BOUND_DELTA_METADATA_KEY = "dagster/lower_bound_delta"
DEADLINE_CRON_METADATA_KEY = "dagster/deadline_cron"
FRESHNESS_TIMEZONE_METADATA_KEY = "dagster/freshness_timezone"
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


def get_last_updated_timestamp(record: Optional[EventLogRecord]) -> Optional[float]:
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


def get_last_update_time_lower_bound(
    deadline_cron: Optional[str],
    current_timestamp: float,
    lower_bound_delta: datetime.timedelta,
    timezone: str,
) -> datetime.datetime:
    """Get the lower bound of the last_update_time for the given cron schedule."""
    current_time_in_freshness_tz = pendulum.from_timestamp(current_timestamp, tz=timezone)
    if deadline_cron:
        return (
            check.not_none(
                get_latest_completed_cron_tick(
                    cron_string=deadline_cron,
                    current_time=current_time_in_freshness_tz,
                    timezone=timezone,
                )
            )
            - lower_bound_delta
        )
    else:
        return current_time_in_freshness_tz - lower_bound_delta


def get_latest_complete_partition_key(
    deadline_cron: Optional[str],
    current_timestamp: float,
    timezone: str,
    partitions_def: Optional[TimeWindowPartitionsDefinition],
) -> Optional[str]:
    """Get the latest complete partition key for the given cron schedule."""
    if not partitions_def:
        return None
    current_time_in_freshness_tz = pendulum.from_timestamp(current_timestamp, tz=timezone)
    latest_cron_tick_time = check.not_none(
        get_latest_completed_cron_tick(
            cron_string=deadline_cron,
            current_time=current_time_in_freshness_tz,
            timezone=timezone,
        )
    )
    latest_cron_tick_time_in_partitions_def_tz = pendulum.from_timestamp(
        latest_cron_tick_time.timestamp(), tz=partitions_def.timezone
    )
    time_window = check.not_none(
        partitions_def.get_prev_partition_window(latest_cron_tick_time_in_partitions_def_tz)
    )
    return partitions_def.get_partition_key_range_for_time_window(time_window).start


def build_freshness_multi_check(
    asset_keys: Sequence[AssetKey],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    lower_bound_delta: datetime.timedelta,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]],
) -> AssetChecksDefinition:
    params_metadata = {}
    if deadline_cron:
        params_metadata[DEADLINE_CRON_METADATA_KEY] = deadline_cron
        params_metadata[FRESHNESS_TIMEZONE_METADATA_KEY] = timezone
    if lower_bound_delta:
        params_metadata[LOWER_BOUND_DELTA_METADATA_KEY] = lower_bound_delta.total_seconds()

    @multi_asset_check(
        specs=[
            AssetCheckSpec(
                "freshness_check",
                asset=asset_key,
                metadata={FRESHNESS_PARAMS_METADATA_KEY: params_metadata},
                description="Evaluates freshness for targeted asset.",
            )
            for asset_key in asset_keys
        ],
        can_subset=True,
        name=f"freshness_check_{unique_id_from_asset_keys(asset_keys)}",
    )
    def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
        for check_key in context.selected_asset_check_keys:
            asset_key = check_key.asset_key
            if asset_property_enforcement_lambda:
                asset_property_enforcement_lambda(
                    context.job_def.asset_layer.asset_graph.get(check_key.asset_key).assets_def
                )
            current_timestamp = pendulum.now("UTC").timestamp()

            # Explicit call to partitions def here will be replaced with AssetSlice reference once it's available.
            partitions_def = cast(
                Optional[TimeWindowPartitionsDefinition],
                context.job_def.asset_layer.asset_graph.get(asset_key).partitions_def,
            )
            check.invariant(
                partitions_def is None
                or isinstance(partitions_def, TimeWindowPartitionsDefinition),
                "Expected partitions_def to be time-windowed.",
            )

            last_update_time_lower_bound = get_last_update_time_lower_bound(
                deadline_cron=deadline_cron,
                timezone=timezone,
                current_timestamp=current_timestamp,
                lower_bound_delta=lower_bound_delta,
            )
            expected_partition_key = get_latest_complete_partition_key(
                deadline_cron=deadline_cron,
                current_timestamp=current_timestamp,
                timezone=timezone,
                partitions_def=partitions_def,
            )
            latest_record = retrieve_latest_record(
                instance=context.instance, asset_key=asset_key, partition_key=expected_partition_key
            )
            update_timestamp = get_last_updated_timestamp(latest_record)
            passed = (
                update_timestamp is not None
                and update_timestamp >= last_update_time_lower_bound.timestamp()
            )

            yield AssetCheckResult(
                passed=passed,
                description=get_description_for_freshness_check_result(
                    passed,
                    update_timestamp,
                    last_update_time_lower_bound,
                    current_timestamp,
                    expected_partition_key,
                ),
                severity=severity,
                asset_key=asset_key,
            )

    return the_check


def get_description_for_freshness_check_result(
    passed: bool,
    update_timestamp: Optional[float],
    last_update_time_lower_bound: datetime.datetime,
    current_timestamp: float,
    expected_partition_key: Optional[str],
) -> str:
    check.invariant(
        (passed and update_timestamp is not None) or not passed,
        "Should not be possible for check to pass without an update to the asset.",
    )
    update_time_delta_str = (
        seconds_in_words(current_timestamp - update_timestamp) if update_timestamp else None
    )
    last_update_time_lower_bound_delta_str = seconds_in_words(
        current_timestamp - last_update_time_lower_bound.timestamp()
    )
    return (
        f"Partition {expected_partition_key} is fresh. Expected the partition to arrive within the last {last_update_time_lower_bound_delta_str}, and it arrived {update_time_delta_str} ago."
        if passed and expected_partition_key
        else f"Partition {expected_partition_key} is overdue. Expected the partition to arrive within the last {last_update_time_lower_bound_delta_str}."
        if not passed and expected_partition_key
        else f"Asset is fresh. Expected an update within the last {last_update_time_lower_bound_delta_str}, and found an update {update_time_delta_str} ago."
        if passed and update_timestamp
        else f"Asset is overdue. Expected an update within the last {last_update_time_lower_bound_delta_str}."
    )


def build_freshness_checks_for_assets(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]] = None,
    lower_bound_delta: datetime.timedelta = datetime.timedelta(minutes=0),
) -> AssetChecksDefinition:
    ensure_no_duplicate_assets(assets)
    deadline_cron = check.opt_str_param(deadline_cron, "deadline_cron")
    check.invariant(
        is_valid_cron_string(deadline_cron) if deadline_cron else True,
        "deadline_cron must be a valid cron string.",
    )
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)
    timezone = check.str_param(timezone, "timezone")
    lower_bound_delta = check.inst_param(lower_bound_delta, "lower_bound_delta", datetime.timedelta)

    return build_freshness_multi_check(
        asset_keys=[asset_key for asset in assets for asset_key in asset_to_keys_iterable(asset)],
        deadline_cron=deadline_cron,
        timezone=timezone,
        severity=severity,
        lower_bound_delta=lower_bound_delta,
        asset_property_enforcement_lambda=asset_property_enforcement_lambda,
    )


def seconds_in_words(delta: float) -> str:
    """Converts the provided number of seconds to a human-readable string.

    Return format is "X days, Y hours, Z minutes, A seconds".
    """
    days = int(delta // 86400)
    hours = int(delta // 3600)
    minutes = int((delta % 3600) // 60)
    seconds = int(delta % 60)
    return ", ".join(
        filter(
            None,
            [
                f"{days} days" if days else None,
                f"{hours} hours" if hours else None,
                f"{minutes} minutes" if minutes else None,
                f"{seconds} seconds" if seconds else None,
            ],
        )
    )


def unique_id_from_asset_keys(asset_keys: Sequence[AssetKey]) -> str:
    """Generate a unique ID from the provided asset keys.

    This is necessary to disambiguate between different ops underlying freshness checks without
    forcing the user to provide a name for the underlying op.
    """
    sorted_asset_keys = sorted(asset_keys, key=lambda asset_key: asset_key.to_string())
    return hashlib.md5(
        ",".join([str(asset_key) for asset_key in sorted_asset_keys]).encode()
    ).hexdigest()[:8]
