import datetime
from typing import Optional, Sequence, Union

from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity

from ..asset_checks import AssetChecksDefinition
from ..assets import AssetsDefinition, SourceAsset
from ..events import CoercibleToAssetKey
from .utils import (
    DEFAULT_FRESHNESS_CRON_TIMEZONE,
    DEFAULT_FRESHNESS_SEVERITY,
    build_freshness_checks_for_assets,
)


@experimental
def build_last_update_freshness_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    lower_bound_delta: datetime.timedelta,
    freshness_cron: Optional[str] = None,
    freshness_cron_timezone: str = DEFAULT_FRESHNESS_CRON_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> Sequence[AssetChecksDefinition]:
    r"""For each provided asset, constructs a freshness check definition.

    This check passes if the asset is considered "fresh" by the time execution begins. An asset is
    considered fresh if a record (i.e. a materialization or observation) exists with an update
    timestamp greater than the "lower bound" derived from the freshness_cron and lower_bound_delta
    parameters. The "lower bound" is defined as the most recent tick of the cron minus
    lower_bound_delta. If no freshness_cron is provided, it is the current time minus
    lower_bound_delta.

    Let's say an asset kicks off materializing at 12:00 PM and takes 10 minutes to complete.
    Allowing for operational constraints and delays, the asset should always be materialized by
    12:30 PM. 12:00 PM provides the lower boundary, since the asset kicks off no earlier than this
    time. Then, we set freshness_cron to "30 12 \* \* \*", which means the asset is expected by
    12:30 PM, and lower_bound_delta to 30, which means the asset can be materialized no earlier
    than 12:00 PM.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The assets to
            construct checks for. For each passed in asset, there will be a corresponding
            constructed `AssetChecksDefinition`.
        lower_bound_delta (datetime.timedelta): The check will pass if the asset was updated within
            lower_bound_delta of the current_time (no cron) or the most recent tick of the cron
            (cron provided).
        freshness_cron (Optional[str]): The check will pass if the asset was updated within
            lower_bound_delta of the most recent tick of this cron.
        freshness_cron_timezone (Optional[str]): The timezone to use for the cron schedule. If not
            provided, the timezone will be UTC.

    Returns:
        Sequence[AssetChecksDefinition]: A list of `AssetChecksDefinition` objects, each
            corresponding to an asset in the `assets` parameter.
    """
    return build_freshness_checks_for_assets(
        assets=assets,
        freshness_cron=freshness_cron,
        freshness_cron_timezone=freshness_cron_timezone,
        severity=severity,
        lower_bound_delta=lower_bound_delta,
    )
