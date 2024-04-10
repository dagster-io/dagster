import datetime
from typing import Any, Callable, Iterable, Optional, Sequence, Union, cast

import pendulum

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity, AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.decorators.asset_check_decorator import (
    multi_asset_check,
)
from dagster._core.definitions.metadata import FloatMetadataValue, TimestampMetadataValue
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.execution.context.compute import (
    AssetCheckExecutionContext,
)
from dagster._utils.schedules import get_latest_completed_cron_tick, is_valid_cron_string

from ..assets import AssetsDefinition, SourceAsset
from ..events import AssetKey, CoercibleToAssetKey
from .utils import (
    DEADLINE_CRON_METADATA_KEY,
    FRESHNESS_PARAMS_METADATA_KEY,
    FRESHNESS_TIMEZONE_METADATA_KEY,
    LAST_UPDATED_TIMESTAMP_METADATA_KEY,
    LOWER_BOUND_DELTA_METADATA_KEY,
    OVERDUE_DEADLINE_TIMESTAMP_METADATA_KEY,
    OVERDUE_SECONDS_METADATA_KEY,
    asset_to_keys_iterable,
    ensure_no_duplicate_assets,
    get_description_for_freshness_check_result,
    get_expected_partition_key,
    get_last_updated_timestamp,
    retrieve_latest_record,
    unique_id_from_asset_keys,
)


def build_freshness_multi_check(
    asset_keys: Sequence[AssetKey],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    lower_bound_delta: datetime.timedelta,
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]],
) -> AssetChecksDefinition:
    params_metadata: dict[str, Any] = {FRESHNESS_TIMEZONE_METADATA_KEY: timezone}
    if deadline_cron:
        params_metadata[DEADLINE_CRON_METADATA_KEY] = deadline_cron
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
            current_time_in_freshness_tz = pendulum.from_timestamp(current_timestamp, tz=timezone)
            latest_completed_cron_tick = get_latest_completed_cron_tick(
                deadline_cron, current_time_in_freshness_tz, timezone
            )
            deadline = check.inst_param(
                latest_completed_cron_tick or current_time_in_freshness_tz,
                "deadline",
                datetime.datetime,
            )
            last_update_time_lower_bound = cast(datetime.datetime, deadline - lower_bound_delta)
            expected_partition_key = get_expected_partition_key(
                deadline=deadline,
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

            metadata = {
                FRESHNESS_PARAMS_METADATA_KEY: params_metadata,
                OVERDUE_DEADLINE_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(
                    deadline.timestamp()
                ),
            }
            if not passed:
                metadata[OVERDUE_SECONDS_METADATA_KEY] = FloatMetadataValue(
                    current_timestamp - deadline.timestamp()
                )
            if update_timestamp:
                metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY] = TimestampMetadataValue(
                    update_timestamp
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
                metadata=metadata,
            )

    return the_check


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
