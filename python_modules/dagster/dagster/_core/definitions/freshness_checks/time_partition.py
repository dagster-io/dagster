from typing import Sequence, Union

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition

from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from .shared_builder import build_freshness_checks_for_assets
from .utils import (
    DEFAULT_FRESHNESS_SEVERITY,
    DEFAULT_FRESHNESS_TIMEZONE,
)


@experimental
def build_time_partition_freshness_checks(
    *,
    assets: Sequence[Union[SourceAsset, CoercibleToAssetKey, AssetsDefinition]],
    deadline_cron: str,
    timezone: str = DEFAULT_FRESHNESS_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> AssetChecksDefinition:
    r"""Construct an `AssetChecksDefinition` that checks the freshness of the provided assets.

    This check passes if the asset is considered "fresh" by the time that execution begins. We
    consider an asset to be "fresh" if there exists a record for the most recent partition, once
    the deadline has passed.

    `deadline_cron` is a cron schedule that defines the deadline for when we should expect the most
    recent partition to arrive by. Once a tick of the cron schedule has passed, this check will fail
    if the most recent partition has not been observed/materialized.

    Let's say I have a daily-partitioned asset which runs every day at 8:00 AM UTC, and takes around
    45 minutes to complete. To account for operational delays, I would expect the asset to be done
    materializing every day by 9:00 AM UTC. I would set the `deadline_cron` to "0 9 \* \* \*". This
    means that starting at 9:00 AM, this check will expect a record to exist for the previous day's
    partition. Note that if the check runs at 8:59 AM, the deadline has not yet passed, and we'll
    instead be checking for the most recently passed deadline, which is yesterday (meaning the
    partition representing the day before yesterday).

    The timestamp of an observation record is the timestamp indicated by the
    "dagster/last_updated_timestamp" metadata key. The timestamp of a materialization record is the
    timestamp at which that record was created.

    The check will fail at runtime if a non-time-window partitioned asset is passed in.

    The check result will contain the following metadata:
    "dagster/freshness_params": A dictionary containing the parameters used to construct the
    check.
    "dagster/last_updated_time": (Only present if the asset has been observed/materialized before)
    The time of the most recent update to the asset.
    "dagster/overdue_seconds": (Only present if asset is overdue) The number of seconds that the
    asset is overdue by.
    "dagster/overdue_deadline_timestamp": The timestamp that we are expecting the asset to have
    arrived by. This is the timestamp of the most recent tick of the cron schedule.

    Examples:
        .. code-block:: python

            from dagster import build_time_partition_freshness_checks, AssetKey
            # A daily partitioned asset that is expected to be updated every day within 45 minutes
            # of 9:00 AM UTC
            from .somewhere import my_daily_scheduled_assets_def

            checks_def = build_time_partition_freshness_checks(
                [my_daily_scheduled_assets_def],
                deadline_cron="0 9 * * *",
            )


    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. For each passed in asset, there will be a corresponding
            constructed `AssetChecksDefinition`.
        deadline_cron (str): The check will pass if the partition time window most recently
            completed by the time of the last cron tick has been observed/materialized.
        timezone (Optional[str]): The timezone to use when calculating freshness and deadline. If
            not provided, defaults to "UTC".

    Returns:
        AssetChecksDefinition: An `AssetChecksDefinition` object, which can execute a freshness
            check for each provided asset.
    """
    return build_freshness_checks_for_assets(
        assets=assets,
        deadline_cron=deadline_cron,
        timezone=timezone,
        severity=severity,
        asset_property_enforcement_lambda=lambda assets_def: check.invariant(
            isinstance(assets_def.partitions_def, TimeWindowPartitionsDefinition),
            "Asset is not time-window partitioned.",
        ),
    )
