from typing import Sequence, Union, cast

import pendulum

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster._core.definitions.metadata import TimestampMetadataValue
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._utils.schedules import get_latest_completed_cron_tick, is_valid_cron_string

from ..asset_check_result import AssetCheckResult
from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from ..time_window_partitions import TimeWindowPartitionsDefinition
from .utils import (
    DEFAULT_FRESHNESS_CRON_TIMEZONE,
    DEFAULT_FRESHNESS_SEVERITY,
    FRESHNESS_CRON_METADATA_KEY,
    FRESHNESS_CRON_TIMEZONE_METADATA_KEY,
    asset_to_keys_iterable,
    ensure_no_duplicate_assets,
    get_last_updated_timestamp,
    retrieve_latest_record,
)

TIME_WINDOW_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY = (
    "dagster/time_window_partitioned_freshness_params"
)


@experimental
def build_freshness_checks_for_time_window_partitioned_assets(
    *,
    assets: Sequence[Union[SourceAsset, CoercibleToAssetKey, AssetsDefinition]],
    freshness_cron: str,
    freshness_cron_timezone: str = DEFAULT_FRESHNESS_CRON_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> Sequence[AssetChecksDefinition]:
    """For each provided time-window partitioned asset, constructs a freshness check definition.

    Will emit a runtime error for any assets that are not time-window partitioned.

    A freshness_cron parameter must be provided to define when a particular partition
    should be considered fresh by.

    For example, let's say I have a daily time-window partitioned asset, and I specify a
    freshness_cron of `0 9 * * *`. This means that I expect March 11 to March 12 data to be seen by
    March 13 9:00 AM. If the data is not seen, the asset check will not pass.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. For each passed in asset, there will be a corresponding
            constructed `AssetChecksDefinition`.
        freshness_cron (str): The check will pass if the partition time window most recently
            completed by the time of the last cron tick has been observed/materialized.
        freshness_cron_timezone (Optional[str]): The timezone to use for the cron schedule. If not
            provided, defaults to "UTC".

    Returns:
        Sequence[AssetChecksDefinition]: A list of `AssetChecksDefinition` objects, each
            corresponding to an asset in the `assets` parameter.
    """
    ensure_no_duplicate_assets(assets)
    freshness_cron = check.str_param(freshness_cron, "freshness_cron")

    check.invariant(
        is_valid_cron_string(freshness_cron),
        "freshness_cron must be a valid cron string.",
    )
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)
    freshness_cron_timezone = check.str_param(freshness_cron_timezone, "freshness_cron_timezone")

    return [
        check
        for asset in assets
        for check in _build_freshness_checks_for_asset(
            asset, freshness_cron, severity, freshness_cron_timezone
        )
    ]


def _build_freshness_checks_for_asset(
    asset: Union[SourceAsset, CoercibleToAssetKey, AssetsDefinition],
    freshness_cron: str,
    severity: AssetCheckSeverity,
    freshness_cron_timezone: str,
) -> Sequence[AssetChecksDefinition]:
    checks = []
    for asset_key in asset_to_keys_iterable(asset):

        @asset_check(
            asset=asset_key,
            description="Evaluates freshness for targeted asset.",
            name="freshness_check",
            metadata={
                TIME_WINDOW_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY: {
                    FRESHNESS_CRON_METADATA_KEY: freshness_cron,
                    FRESHNESS_CRON_TIMEZONE_METADATA_KEY: freshness_cron_timezone,
                }
            },
        )
        def the_check(context: AssetExecutionContext) -> AssetCheckResult:
            current_time = pendulum.now()
            current_timestamp = check.float_param(current_time.timestamp(), "current_time")
            partitions_def: TimeWindowPartitionsDefinition = cast(
                TimeWindowPartitionsDefinition,
                check.inst_param(
                    context.job_def.asset_layer.asset_graph.get(asset_key).partitions_def,
                    "partitions_def",
                    TimeWindowPartitionsDefinition,
                ),
            )
            latest_cron_tick_time = check.not_none(
                get_latest_completed_cron_tick(
                    freshness_cron, current_time, freshness_cron_timezone
                ),
                "expected there to be a previous tick of the provided cron",
            )

            time_window = partitions_def.get_prev_partition_window(latest_cron_tick_time)
            if not time_window:
                return AssetCheckResult(
                    passed=True,
                    description="No partitions have been completed yet.",
                    severity=severity,
                )
            partition_key = partitions_def.get_partition_key_range_for_time_window(
                time_window
            ).start
            latest_record = retrieve_latest_record(context.instance, asset_key, partition_key)
            passed = latest_record is not None
            expected_partition_key = partitions_def.get_partition_key_for_timestamp(
                time_window.start.timestamp()
            )
            if passed:
                last_updated_timestamp = check.float_param(
                    get_last_updated_timestamp(latest_record), "last_updated_timestamp"
                )
                metadata = {
                    "dagster/last_updated_timestamp": TimestampMetadataValue(
                        last_updated_timestamp
                    ),
                }
                description = f"Partition {expected_partition_key} arrived on time. "
            else:
                minutes_late = (current_timestamp - latest_cron_tick_time.timestamp()) // 60
                metadata = {
                    "dagster/minutes_late": TimestampMetadataValue(minutes_late),
                }
                description = f"Partition {expected_partition_key} is {minutes_late} minutes late."

            return AssetCheckResult(
                passed=passed,
                description=description,
                metadata=metadata,
                severity=severity,
            )

        checks.append(the_check)
    return checks
