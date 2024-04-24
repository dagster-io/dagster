import datetime
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Union, cast

import pendulum

from dagster import _check as check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity, AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.decorators.asset_check_decorator import (
    multi_asset_check,
)
from dagster._core.definitions.metadata import (
    FloatMetadataValue,
    JsonMetadataValue,
    MetadataValue,
    TimestampMetadataValue,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.execution.context.compute import (
    AssetCheckExecutionContext,
)
from dagster._utils.schedules import (
    get_latest_completed_cron_tick,
    get_next_cron_tick,
    is_valid_cron_string,
)

from ..assets import AssetsDefinition, SourceAsset
from ..events import AssetKey, CoercibleToAssetKey
from .utils import (
    DEADLINE_CRON_PARAM_KEY,
    EXPECTED_BY_TIMESTAMP_METADATA_KEY,
    FRESH_UNTIL_METADATA_KEY,
    FRESHNESS_PARAMS_METADATA_KEY,
    LAST_UPDATED_TIMESTAMP_METADATA_KEY,
    LOWER_BOUND_DELTA_PARAM_KEY,
    OVERDUE_SECONDS_METADATA_KEY,
    TIMEZONE_PARAM_KEY,
    asset_to_keys_iterable,
    ensure_no_duplicate_assets,
    get_description_for_freshness_check_result,
    get_last_updated_timestamp,
    retrieve_latest_record,
    unique_id_from_asset_keys,
)


def build_freshness_multi_check(
    asset_keys: Sequence[AssetKey],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    lower_bound_delta: Optional[datetime.timedelta],
    asset_property_enforcement_lambda: Optional[Callable[[AssetsDefinition], bool]],
) -> AssetChecksDefinition:
    params_metadata: dict[str, Any] = {TIMEZONE_PARAM_KEY: timezone}
    if deadline_cron:
        params_metadata[DEADLINE_CRON_PARAM_KEY] = deadline_cron
    if lower_bound_delta:
        params_metadata[LOWER_BOUND_DELTA_PARAM_KEY] = lower_bound_delta.total_seconds()

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
            latest_completed_cron_tick = (
                get_latest_completed_cron_tick(
                    deadline_cron, current_time_in_freshness_tz, timezone
                )
                if deadline_cron
                else None
            )
            deadline = check.inst_param(
                latest_completed_cron_tick or current_time_in_freshness_tz,
                "deadline",
                datetime.datetime,
            )
            if not partitions_def:
                last_completed_time_window = None
                expected_partition_key = None
            else:
                deadline_in_partitions_def_tz = pendulum.from_timestamp(
                    deadline.timestamp(), tz=partitions_def.timezone
                )
                last_completed_time_window = check.not_none(
                    partitions_def.get_prev_partition_window(deadline_in_partitions_def_tz)
                )
                expected_partition_key = partitions_def.get_partition_key_range_for_time_window(
                    last_completed_time_window
                ).start

            if lower_bound_delta:
                last_update_time_lower_bound = cast(datetime.datetime, deadline - lower_bound_delta)
            else:
                last_update_time_lower_bound = check.not_none(
                    last_completed_time_window,
                    "Expected a valid partitioned asset with a completed time window in order to determine valid freshness window.",
                ).end

            latest_record = retrieve_latest_record(
                instance=context.instance, asset_key=asset_key, partition_key=expected_partition_key
            )
            update_timestamp = get_last_updated_timestamp(latest_record, context)
            passed = (
                update_timestamp is not None
                and update_timestamp >= last_update_time_lower_bound.timestamp()
            )

            metadata: Dict[str, MetadataValue] = {
                FRESHNESS_PARAMS_METADATA_KEY: JsonMetadataValue(params_metadata),
            }
            if not passed:
                metadata[OVERDUE_SECONDS_METADATA_KEY] = FloatMetadataValue(
                    current_timestamp - deadline.timestamp()
                )
                expected_by = (
                    deadline.timestamp()
                    if deadline_cron
                    else update_timestamp + check.not_none(lower_bound_delta).total_seconds()
                    if update_timestamp
                    else None
                )
                if expected_by:
                    metadata[EXPECTED_BY_TIMESTAMP_METADATA_KEY] = TimestampMetadataValue(
                        expected_by
                    )
            else:
                # If the asset is fresh, we can potentially determine when it has the possibility of becoming stale again.
                # In the case of a deadline cron, this is the next cron tick after the current time.
                # In the case of just a lower_bound_delta, this is the last update time plus the
                # lower_bound_delta.
                fresh_until = (
                    check.not_none(
                        get_next_cron_tick(deadline_cron, current_time_in_freshness_tz, timezone)
                    ).timestamp()
                    if deadline_cron
                    else check.not_none(update_timestamp)
                    + check.not_none(lower_bound_delta).total_seconds()
                )
                metadata[FRESH_UNTIL_METADATA_KEY] = TimestampMetadataValue(fresh_until)
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
                    record_arrival_timestamp=latest_record.timestamp if latest_record else None,
                    event_type=latest_record.event_type if latest_record else None,
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
    lower_bound_delta: Optional[datetime.timedelta] = None,
) -> AssetChecksDefinition:
    ensure_no_duplicate_assets(assets)
    deadline_cron = check.opt_str_param(deadline_cron, "deadline_cron")
    check.invariant(
        is_valid_cron_string(deadline_cron) if deadline_cron else True,
        "deadline_cron must be a valid cron string.",
    )
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)
    timezone = check.str_param(timezone, "timezone")
    check.opt_inst_param(lower_bound_delta, "lower_bound_delta", datetime.timedelta)

    return build_freshness_multi_check(
        asset_keys=[asset_key for asset in assets for asset_key in asset_to_keys_iterable(asset)],
        deadline_cron=deadline_cron,
        timezone=timezone,
        severity=severity,
        lower_bound_delta=lower_bound_delta,
        asset_property_enforcement_lambda=asset_property_enforcement_lambda,
    )
