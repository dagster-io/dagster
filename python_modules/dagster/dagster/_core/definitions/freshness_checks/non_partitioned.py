from typing import Any, Dict, Optional, Sequence, Union

import pendulum

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.metadata import (
    MetadataValue,
    TimestampMetadataValue,
)
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._utils.schedules import get_latest_completed_cron_tick, is_valid_cron_string

from ..asset_check_result import AssetCheckResult
from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..decorators.asset_check_decorator import asset_check
from ..events import CoercibleToAssetKey
from .utils import (
    DEFAULT_FRESHNESS_CRON_TIMEZONE,
    DEFAULT_FRESHNESS_SEVERITY,
    FRESHNESS_CRON_METADATA_KEY,
    FRESHNESS_CRON_TIMEZONE_METADATA_KEY,
    MAXIMUM_LAG_METADATA_KEY,
    asset_to_keys_iterable,
    ensure_no_duplicate_assets,
    get_last_updated_timestamp,
    retrieve_latest_record,
)

NON_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY = "dagster/non_partitioned_freshness_params"


@experimental
def build_freshness_checks_for_non_partitioned_assets(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    maximum_lag_minutes: int,
    freshness_cron: Optional[str] = None,
    freshness_cron_timezone: str = DEFAULT_FRESHNESS_CRON_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> Sequence[AssetChecksDefinition]:
    r"""For each provided asset, constructs a freshness check definition.

    Only accepts assets that have no partitions definition. For time window partitioned assets, see
    `build_freshness_checks_for_time_window_partitioned_assets`. Providing partitioned assets to
    this function will result in a runtime error.

    An asset is considered fresh if it has been materialized or observed within a certain time
    window. The freshness_cron and maximum_lag_minutes parameters are used to define this time
    window. Freshness_cron defines the time at which the asset should have been materialized, and
    maximum_lag_minutes provides a tolerance for the range at which the asset can arrive.

    Let's say an asset kicks off materializing at 12:00 PM and takes 10 minutes to complete.
    Allowing for operational constraints and delays, the asset should always be materialized by
    12:30 PM. 12:00 PM provides the lower boundary, since the asset kicks off no earlier than this
    time. Then, we set freshness_cron to "30 12 \* \* \*", which means the asset is expected by
    12:30 PM, and maximum_lag_minutes to 30, which means the asset can be materialized no earlier
    than 12:00 PM.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. For each passed in asset, there will be a corresponding
            constructed `AssetChecksDefinition`.
        maximum_lag_minutes (int): The check will pass if the asset was updated within
            maximum_lag_minutes of the current_time (no cron) or the most recent tick of the cron
            (cron provided).
        freshness_cron (Optional[str]): The check will pass if the asset was updated within
            maximum_lag_minutes of the most recent tick of this cron.
        freshness_cron_timezone (Optional[str]): The timezone to use for the cron schedule. If not
            provided, the timezone will be UTC.

    Returns:
        Sequence[AssetChecksDefinition]: A list of `AssetChecksDefinition` objects, each
            corresponding to an asset in the `assets` parameter.
    """
    ensure_no_duplicate_assets(assets)
    freshness_cron = check.opt_str_param(freshness_cron, "freshness_cron")
    check.param_invariant(
        is_valid_cron_string(freshness_cron) if freshness_cron else True,
        "freshness_cron",
        "Expect a valid cron string.",
    )
    freshness_cron_timezone = check.str_param(freshness_cron_timezone, "freshness_cron_timezone")
    maximum_lag_minutes = check.int_param(maximum_lag_minutes, "maximum_lag_minutes")
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)

    return [
        check
        for asset in assets
        for check in _build_freshness_check_for_assets(
            asset,
            freshness_cron=freshness_cron,
            maximum_lag_minutes=maximum_lag_minutes,
            severity=severity,
            freshness_cron_timezone=freshness_cron_timezone,
        )
    ]


def _build_freshness_check_for_assets(
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
    freshness_cron: Optional[str],
    maximum_lag_minutes: int,
    severity: AssetCheckSeverity,
    freshness_cron_timezone: str,
) -> Sequence[AssetChecksDefinition]:
    params_metadata: Dict[str, Any] = {MAXIMUM_LAG_METADATA_KEY: maximum_lag_minutes}
    if freshness_cron:
        params_metadata[FRESHNESS_CRON_METADATA_KEY] = freshness_cron
        params_metadata[FRESHNESS_CRON_TIMEZONE_METADATA_KEY] = freshness_cron_timezone
    checks = []
    for asset_key in asset_to_keys_iterable(asset):

        @asset_check(
            asset=asset,
            description=f"Evaluates freshness for targeted asset. Cron: {freshness_cron}, Maximum "
            f"lag minutes: {maximum_lag_minutes}.",
            name="freshness_check",
            metadata={NON_PARTITIONED_FRESHNESS_PARAMS_METADATA_KEY: params_metadata},
        )
        def the_check(context: AssetExecutionContext) -> AssetCheckResult:
            check.invariant(
                context.job_def.asset_layer.asset_graph.get(asset_key).partitions_def is None,
                "Expected non-partitioned asset",
            )

            current_time = pendulum.now("UTC")
            current_timestamp = check.float_param(current_time.timestamp(), "current_time")
            latest_cron_tick = get_latest_completed_cron_tick(
                freshness_cron, current_time, freshness_cron_timezone
            )
            lower_search_bound = pendulum.instance(latest_cron_tick or current_time).subtract(
                minutes=maximum_lag_minutes
            )
            latest_record = retrieve_latest_record(context.instance, asset_key, partition_key=None)
            last_updated_timestamp = get_last_updated_timestamp(latest_record)

            if last_updated_timestamp is None:
                passed = True
                metadata = {}
                description = "Could not determine last updated timestamp"
            else:
                passed = lower_search_bound.timestamp() <= last_updated_timestamp
                metadata = {
                    "dagster/last_updated_timestamp": MetadataValue.timestamp(
                        last_updated_timestamp
                    )
                }

                if passed:
                    description = None
                else:
                    if latest_cron_tick is None:
                        description = f"Last update was more than {maximum_lag_minutes} minutes ago"
                    else:
                        description = f"Last update was more than {maximum_lag_minutes} minutes before last cron tick"
                        metadata["dagster/latest_cron_tick"] = MetadataValue.timestamp(
                            latest_cron_tick
                        )
                    metadata["dagster/minutes_late"] = TimestampMetadataValue(
                        (current_timestamp - last_updated_timestamp) // 60
                    )

            return AssetCheckResult(
                passed=passed, severity=severity, description=description, metadata=metadata
            )

        checks.append(the_check)

    return checks
