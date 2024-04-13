import datetime
from typing import Optional, Sequence, Union

from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity

from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from .shared_builder import build_freshness_checks_for_assets
from .utils import (
    DEFAULT_FRESHNESS_SEVERITY,
    DEFAULT_FRESHNESS_TIMEZONE,
)


@experimental
def build_last_update_freshness_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    lower_bound_delta: datetime.timedelta,
    deadline_cron: Optional[str] = None,
    timezone: str = DEFAULT_FRESHNESS_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> AssetChecksDefinition:
    r"""Constructs an `AssetChecksDefinition` that checks the freshness of the provided assets.

    This check passes if the asset is found to be "fresh", and fails if the asset is found to be
    "overdue". An asset is considered fresh if a record (i.e. a materialization or observation)
    exists with a timestamp greater than the "lower bound" derived from the parameters of this
    function.

    `deadline_cron` is a cron schedule that defines the deadline for when we should expect the asset
    to arrive by; if not provided, we consider the deadline to be the execution time of the check.
    `lower_bound_delta` is a timedelta that defines the lower bound for when a record could have
    arrived by. If the most recent recent record's timestamp is earlier than
    `deadline-lower_bound_delta`, the asset is considered overdue.

    Let's use two examples, one with a deadline_cron set and one without.
    Let's say I have an asset which runs on a schedule every day at 8:00 AM UTC, and usually takes
    around 45 minutes to complete. To account for operational delays, I would expect the asset to be
    done materializing every day by 9:00 AM UTC. I would set the `deadline_cron` to "0 9 \* \* \*", and
    the `lower_bound_delta` to "45 minutes". This would mean that starting at 9:00 AM, this check
    will expect a materialization record to have been created no earlier than 8:15 AM. Note that if
    the check runs at 8:59 AM, the deadline has not yet passed, and we'll instead be checking for
    the most recently passed deadline, which is yesterday.
    Let's say I have an observable source asset on a data source which I expect should never be more
    than 3 hours out of date. In this case, there's no fixed schedule for when the data should be
    updated, so I would not provide a `deadline_cron`. Instead, I would set the `lower_bound_delta`
    parameter to "3 hours". This would mean that the check will expect the most recent observation
    record to indicate data no older than 3 hours, relative to the current time, regardless of when it runs.

    The check result will contain the following metadata:
    "dagster/freshness_params": A dictionary containing the parameters used to construct the
    check
    "dagster/last_updated_time": The time of the most recent update to the asset
    "dagster/overdue_seconds": (Only present if asset is overdue) The number of seconds that the
    asset is overdue by.
    "dagster/overdue_deadline_timestamp": The timestamp that we are expecting the asset to have
    arrived by. In the case of a provided deadline_cron, this is the timestamp of the most recent
    tick of the cron schedule. In the case of no deadline_cron, this is the current time.

    Examples:
        .. code-block:: python

            # Example 1: Assets that are expected to be updated every day within 45 minutes of
            # 9:00 AM UTC
            from dagster import build_last_update_freshness_checks, AssetKey
            from .somewhere import my_daily_scheduled_assets_def

            checks_def = build_last_update_freshness_checks(
                [my_daily_scheduled_assets_def, AssetKey("my_other_daily_asset_key")],
                lower_bound_delta=datetime.timedelta(minutes=45),
                deadline_cron="0 9 * * *",
            )

            # Example 2: Assets that are expected to be updated within 3 hours of the current time
            from dagster import build_last_update_freshness_checks, AssetKey
            from .somewhere import my_observable_source_asset

            checks_def = build_last_update_freshness_checks(
                [my_observable_source_asset, AssetKey("my_other_observable_asset_key")],
                lower_bound_delta=datetime.timedelta(hours=3),
            )


    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. All checks are incorporated into the same `AssetChecksDefinition`,
            which can be subsetted to run checks for specific assets.
        lower_bound_delta (datetime.timedelta): The check will pass if the asset was updated within
            lower_bound_delta of the current_time (no cron) or the most recent tick of the cron
            (cron provided).
        deadline_cron (Optional[str]): Defines the deadline for when we should start checking
            that the asset arrived. If not provided, the deadline is the execution time of the check.
        timezone (Optional[str]): The timezone to use when calculating freshness and deadline. If
            not provided, defaults to "UTC".

    Returns:
        AssetChecksDefinition: An `AssetChecksDefinition` object, which can execute a freshness check
            for all provided assets.
    """
    return build_freshness_checks_for_assets(
        assets=assets,
        deadline_cron=deadline_cron,
        timezone=timezone,
        severity=severity,
        lower_bound_delta=lower_bound_delta,
    )
