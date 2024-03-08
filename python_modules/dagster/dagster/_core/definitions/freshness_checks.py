from datetime import datetime
from typing import Optional, Sequence, Union, cast

import pendulum

from dagster import _check as check
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.data_time import DATA_TIME_METADATA_KEY
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance import DagsterInstance
from dagster._utils.schedules import is_valid_cron_string, reverse_cron_string_iterator

from .asset_check_result import AssetCheckResult
from .asset_checks import AssetChecksDefinition
from .assets import AssetsDefinition, SourceAsset
from .events import AssetKey, CoercibleToAssetKey
from .partition import PartitionsDefinition
from .time_window_partitions import TimeWindowPartitionsDefinition

DEFAULT_FRESHNESS_SEVERITY = AssetCheckSeverity.WARN


def build_freshness_checks(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    freshness_cron: Optional[str] = None,
    maximum_lag_minutes: Optional[int] = None,
    severity: Optional[AssetCheckSeverity] = None,
) -> Sequence[AssetChecksDefinition]:
    """For each provided asset, constructs a freshness check definition.

    An asset is considered fresh if it has been materialized or observed within a certain time window.
    The freshness_cron and maximum_lag_minutes parameters are used to define this time window.
    freshness_cron defines the time at which the asset should have been materialized, and maximum_lag_minutes provides a tolerance for the range at which the asset can arrive.

    Let's say an asset kicks off materializing at 12:00 PM and takes 10 minutes to complete.
    Allowing for operational constraints and delays, the asset should always be materialized by 12:30 PM.
    12:00 PM provides the lower boundary, since the asset kicks off no earlier than this time.
    Then, we set freshness_cron to "30 12 * * *", which means the asset is expected by 12:30 PM, and maximum_lag_minutes to 30,
    which means the asset can be materialized no earlier than 12:00 PM.

    A time-window partitioned asset is considered fresh if the latest completed time window is materialized or observed.
    The freshness_cron parameter can be used to influence the time window that is checked. For example, if I have a daily partitioned asset,
    and I specify a freshness_cron for 12:00 PM, and I run the check at 1:00 AM March 12, I will check for the time window
    March 10 12:00 AM - March 11 12:00 AM, since the most recent completed tick of the cron was at 12:00 PM March 11.
    For partitioned assets, the maximum_lag_minutes parameter is not used.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to construct checks for. For each passed in
            asset, there will be a corresponding constructed `AssetChecksDefinition`.
        freshness_cron (Optional[str]): The cron for which freshness is defined.
        maximum_lag_minutes (Optional[int]): The maximum lag in minutes that is acceptable for the asset.

    Returns:
        Sequence[AssetChecksDefinition]: A list of `AssetChecksDefinition` objects, each corresponding to an asset in the `assets` parameter.
    """
    duplicate_assets = find_duplicate_assets(assets)
    check.invariant(
        len(duplicate_assets) == 0,
        f"Found duplicate assets in the provided list of assets: {duplicate_assets}. Please ensure that each asset is unique.",
    )
    freshness_cron = check.opt_str_param(freshness_cron, "freshness_cron")
    check.param_invariant(
        is_valid_cron_string(freshness_cron) if freshness_cron else True,
        "freshness_cron",
        "Expect a valid cron string.",
    )
    maximum_lag_minutes = check.opt_int_param(maximum_lag_minutes, "maximum_lag_minutes")
    check.invariant(
        freshness_cron is not None or maximum_lag_minutes is not None,
        "At least one of freshness_cron or maximum_lag_minutes must be provided.",
    )
    severity = check.opt_inst_param(
        severity, "severity", AssetCheckSeverity, DEFAULT_FRESHNESS_SEVERITY
    )

    return [
        _build_freshness_check_for_asset(
            asset,
            freshness_cron=freshness_cron,
            maximum_lag_minutes=maximum_lag_minutes,
            severity=severity,
        )
        for asset in assets
    ]


def _build_freshness_check_for_asset(
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
    freshness_cron: Optional[str],
    maximum_lag_minutes: Optional[int],
    severity: AssetCheckSeverity,
) -> AssetChecksDefinition:
    from .decorators.asset_check_decorator import asset_check

    asset_key = AssetKey.from_coercible_or_definition(asset)

    freshness_cron = check.opt_str_param(freshness_cron, "freshness_cron")
    maximum_lag_minutes = check.opt_int_param(maximum_lag_minutes, "maximum_lag_minutes")

    @asset_check(
        asset=asset,
        description=f"Evaluates freshness for targeted asset. Cron: {freshness_cron}, Maximum lag: {maximum_lag_minutes}.",
        name="freshness_check",
    )
    def the_check(context: AssetExecutionContext) -> AssetCheckResult:
        current_time = pendulum.now("UTC")
        partitions_def = ensure_non_partitioned_or_time_window_partitioned_asset(
            asset_key, context.job_def.asset_layer.partitions_def_for_asset(asset_key)
        )
        if partitions_def:
            upper_partition_bound = (
                get_latest_completed_cron_tick(
                    freshness_cron, current_time, partitions_def.timezone
                )
                or current_time
            )
            relevant_partition = get_latest_completed_partition(
                partitions_def, upper_partition_bound
            )
            record_for_partition = retrieve_latest_record(
                context.instance,
                asset_key,
                relevant_partition,
            )
            passed = record_for_partition is not None
            description = f"Failed due to missing materialization/observation for partition {relevant_partition}."
        else:
            lower_search_bound = pendulum.instance(
                get_latest_completed_cron_tick(freshness_cron, current_time, None) or current_time
            ).subtract(minutes=maximum_lag_minutes or 0)

            latest_record = retrieve_latest_record(
                context.instance,
                asset_key,
                partition_key=None,
            )
            passed = (
                latest_record is not None
                and lower_search_bound.timestamp() <= latest_record.timestamp
            )
            description = (
                f"Failed due to no materialization/observation after {lower_search_bound.to_date_string()}."
                if latest_record is None
                else f"Failed due to materialization/observation after {lower_search_bound.to_date_string()}."
            )
        return AssetCheckResult(
            passed=passed,
            severity=severity,
            metadata={
                "description": description,
            },
        )

    return the_check


def get_latest_completed_cron_tick(
    freshness_cron: Optional[str], current_time: datetime, timezone: Optional[str]
) -> Optional[datetime]:
    if not freshness_cron:
        return None

    cron_iter = reverse_cron_string_iterator(
        end_timestamp=current_time.timestamp(),
        cron_string=freshness_cron,
        execution_timezone=timezone,
    )
    return pendulum.instance(next(cron_iter))


def ensure_non_partitioned_or_time_window_partitioned_asset(
    asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]
) -> Optional[TimeWindowPartitionsDefinition]:
    check.inst_param(asset_key, "asset_key", AssetKey)
    check.opt_inst_param(partitions_def, "partitions_def", PartitionsDefinition)

    if partitions_def and not isinstance(partitions_def, TimeWindowPartitionsDefinition):
        raise DagsterInvariantViolationError(
            "Only non-partitioned and time window-partitioned assets are currently supported for `build_freshness_checks`."
        )
    return cast(Optional[TimeWindowPartitionsDefinition], partitions_def)


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


def get_latest_completed_partition(
    partitions_def: Optional[TimeWindowPartitionsDefinition], upper_bound: datetime
) -> Optional[str]:
    if partitions_def is None:
        return None
    time_window = partitions_def.get_prev_partition_window(upper_bound)
    if not time_window:
        return None
    return partitions_def.get_partition_key_range_for_time_window(time_window).start


def retrieve_timestamp_from_record(asset_record: EventLogRecord) -> float:
    """Retrieve the timestamp from the given materialization or observation record."""
    check.inst_param(asset_record, "asset_record", EventLogRecord)
    if asset_record.event_log_entry.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION:
        return asset_record.timestamp
    else:
        metadata = check.not_none(asset_record.asset_observation).metadata
        return check.float_param(metadata[DATA_TIME_METADATA_KEY].value, "data_time")


def find_duplicate_assets(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
) -> Sequence[AssetKey]:
    """Finds duplicate assets in the provided list of assets.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]): The assets to check for duplicates.

    Returns:
        Sequence[AssetKey]: A list of the duplicate assets.
    """
    asset_keys = [AssetKey.from_coercible_or_definition(asset) for asset in assets]
    return [asset_key for asset_key in asset_keys if asset_keys.count(asset_key) > 1]
