from typing import Sequence, Union

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition

from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from .utils import (
    DEFAULT_FRESHNESS_SEVERITY,
    DEFAULT_UPPER_BOUND_CRON_TIMEZONE,
    build_freshness_checks_for_assets,
)


@experimental
def build_time_partition_freshness_checks(
    *,
    assets: Sequence[Union[SourceAsset, CoercibleToAssetKey, AssetsDefinition]],
    upper_bound_cron: str,
    upper_bound_cron_timezone: str = DEFAULT_UPPER_BOUND_CRON_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
    fail_on_late_arrival: bool = False,
) -> Sequence[AssetChecksDefinition]:
    """For each provided time-window partitioned asset, constructs a freshness check definition.

    We define a time window in which a record
    (i.e. materialization or observation) for the asset's most
    recently completed partition is expected to arrive. This time window is bounded above by the
    most recent tick of the `upper_bound_cron` schedule, and below by the start of the partition that most
    recently completed before that cron tick. If no update is observed within this time window, the
    asset is considered overdue.

    There are two ways an asset can be overdue; either the most recent completed partition has not arrived at all by
    the end of the time window (i.e. missing), or the partition was updated after the time window ended (i.e. late
    arrival). The check will always fail for a missing partition, but the user has the option to either
    fail the check or pass it for a late arrival using the `fail_on_late_arrival` parameter.

    To give a concrete example of how these parameters interplay, let's say I have a daily
    time-window partitioned asset, and I expect the previous day's partition to be materialized by 9:00 AM the next day.
    We therefore set `upper_bound_cron` to "0 9 * * *". Occasionally, the job may be delayed due to
    infrastructural issues, so we set `fail_on_late_arrival` to False to allow the check to start passing again once the asset is updated.

    Let's say that initially, the check runs at 9:01 AM and the previous day's partition has not been
    materialized. The check will search for the most recent record for this partition, and there is no record to be found, so the check fails.
    Then, we have a record for the partition arrive at 9:10 AM, and re-run the check at 9:11 AM. The
    most recent record is a late arrival, but we have set `fail_on_late_arrival` to False, so the check passes.
    The check will fail at runtime if a non-time-window partitioned asset is passed in to this function.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. For each passed in asset, there will be a corresponding
            constructed `AssetChecksDefinition`.
        upper_bound_cron (str): The check will pass if a record for the partition most recently completed by the last tick of this cron, arrived before that tick.
        upper_bound_cron_timezone (Optional[str]): The timezone to use for the cron schedule. If not
            provided, defaults to "UTC".
        fail_on_late_arrival (bool): If True, the check will fail if the partition arrived only after
        the time window ended.

    Returns:
        Sequence[AssetChecksDefinition]: A list of `AssetChecksDefinition` objects, each
            corresponding to an asset in the `assets` parameter.
    """
    return build_freshness_checks_for_assets(
        assets=assets,
        upper_bound_cron=upper_bound_cron,
        upper_bound_cron_timezone=upper_bound_cron_timezone,
        severity=severity,
        asset_property_enforcement_lambda=lambda assets_def: check.invariant(
            isinstance(assets_def.partitions_def, TimeWindowPartitionsDefinition),
            "Asset is not time-window partitioned.",
        ),
        fail_on_late_arrival=fail_on_late_arrival,
    )
