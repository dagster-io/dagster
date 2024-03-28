import datetime
from typing import Optional, Sequence, Union

from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity

from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from .utils import (
    DEFAULT_FRESHNESS_SEVERITY,
    DEFAULT_UPPER_BOUND_CRON_TIMEZONE,
    build_freshness_checks_for_assets,
)


@experimental
def build_last_update_freshness_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    time_window_size: datetime.timedelta,
    upper_bound_cron: Optional[str] = None,
    upper_bound_cron_timezone: str = DEFAULT_UPPER_BOUND_CRON_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
    fail_on_late_arrival: bool = False,
) -> Sequence[AssetChecksDefinition]:
    r"""For each provided asset, constructs a freshness check definition.

    The parameters of this check define a time window in which a record for the asset is expected to arrive.
    If no record arrives within this time window, the asset is considered overdue.

    There are two ways an asset can be overdue; either there has been no record for the asset at all from
    the beginning of the time window (i.e. missing) to the time of execution of this check, or the
    asset arrived after the time window ended (i.e. late arrival). The check will always fail
    for a missing record, but the user has the option to either fail the check or pass it for a late arrival using the `fail_on_late_arrival` parameter.

    `time_window_size` defines the length of the time window in which the asset is expected. The
    upper bound of the time window is the most recent tick of the `upper_bound_cron` cron schedule,
    or in the case of no cron schedule, the current time. The lower bound of the time window is then
    the upper bound minus `time_window_size`.

    To give a concrete example of how these parameters interplay, let's say we have an asset that we
    expect to arrive every day by 9:00 AM. The job materializing this asset starts at 8:00 AM,
    so the earliest we can expect the asset to have a relevant record is 8:00 AM. We therefore set
    `upper_bound_cron` to "0 9 * * *" and `time_window_size` to 1 hour. Occasionally, the job may
    be delayed due to infrastructural issues, and so we set `fail_on_late_arrival` to False to allow
    the check to start passing again once the asset arrives.

    Let's say that initially, the check runs at 9:01 AM and the asset hasn't arrived. The
    check will search for the most recent record for the asset, and the most recent record is before
    this time window, so the check fails. Then, we have a new record arrive at 9:10 AM, and re-run
    the check at 9:11 AM. The most recent record is a late arrival, but we have set
    `fail_on_late_arrival` to False, so the check passes.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. For each passed in asset, there will be a corresponding
            constructed `AssetChecksDefinition`.
        time_window_size (datetime.timedelta): The check will pass if the asset arrives within
            time_window_size of the current_time (no upper_bound_cron) or the most recent tick of
            the cron (upper_bound_cron provided).
        upper_bound_cron (Optional[str]): The check will pass if the asset arrives within
            `time_window_size` of the most recent completed tick of this cron.
        upper_bound_cron_timezone (Optional[str]): The timezone to use for the cron schedule. If not
            provided, the timezone will be UTC.

    Returns:
        Sequence[AssetChecksDefinition]: A list of `AssetChecksDefinition` objects, each
            corresponding to an asset in the `assets` parameter.
    """
    return build_freshness_checks_for_assets(
        assets=assets,
        upper_bound_cron=upper_bound_cron,
        upper_bound_cron_timezone=upper_bound_cron_timezone,
        severity=severity,
        time_window_size=time_window_size,
        fail_on_late_arrival=fail_on_late_arrival,
    )
