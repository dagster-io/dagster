from typing import Sequence, Union

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition

from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from .utils import (
    DEFAULT_FRESHNESS_CRON_TIMEZONE,
    DEFAULT_FRESHNESS_SEVERITY,
    build_freshness_checks_for_assets,
)


@experimental
def build_time_partition_freshness_checks(
    *,
    assets: Sequence[Union[SourceAsset, CoercibleToAssetKey, AssetsDefinition]],
    freshness_cron: str,
    freshness_cron_timezone: str = DEFAULT_FRESHNESS_CRON_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> Sequence[AssetChecksDefinition]:
    """For each provided time-window partitioned asset, constructs a freshness check definition.

    This check passes if the asset is considered "fresh" by the time that execution begins. We
    consider an asset to be "fresh" if the most recent partition which has completed before the most
    recent tick of the cron has been recorded (i.e. materialized or observed).

    Let's say I have a daily time-window partitioned asset, I specify a freshness_cron of
    `0 9 * * *`, and I am executing the asset check at 10:00 AM on March 13. This means that I
    fail if the partition representing March 11 to March 12 has not been seen materialized yet.

    The check will fail at runtime if a non-time-window partitioned asset is passed in.

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
    return build_freshness_checks_for_assets(
        assets=assets,
        freshness_cron=freshness_cron,
        freshness_cron_timezone=freshness_cron_timezone,
        severity=severity,
        asset_property_enforcement_lambda=lambda assets_def: check.invariant(
            isinstance(assets_def.partitions_def, TimeWindowPartitionsDefinition),
            "Asset is not time-window partitioned.",
        ),
    )
