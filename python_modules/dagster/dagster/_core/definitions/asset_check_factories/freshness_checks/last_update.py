import datetime
from collections.abc import Iterable, Sequence
from typing import Any, Optional, Union, cast

from dagster import _check as check
from dagster._annotations import beta
from dagster._core.definitions.asset_check_factories.utils import (
    DEADLINE_CRON_PARAM_KEY,
    DEFAULT_FRESHNESS_SEVERITY,
    DEFAULT_FRESHNESS_TIMEZONE,
    FRESH_UNTIL_METADATA_KEY,
    FRESHNESS_PARAMS_METADATA_KEY,
    LAST_UPDATED_TIMESTAMP_METADATA_KEY,
    LATEST_CRON_TICK_METADATA_KEY,
    LOWER_BOUND_DELTA_PARAM_KEY,
    LOWER_BOUND_TIMESTAMP_METADATA_KEY,
    TIMEZONE_PARAM_KEY,
    assets_to_keys,
    ensure_no_duplicate_assets,
    freshness_multi_asset_check,
    retrieve_last_update_record,
    retrieve_timestamp_from_record,
    seconds_in_words,
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.metadata import (
    JsonMetadataValue,
    MetadataValue,
    TimestampMetadataValue,
)
from dagster._core.execution.context.compute import AssetCheckExecutionContext
from dagster._time import get_current_timestamp, get_timezone
from dagster._utils.schedules import (
    get_latest_completed_cron_tick,
    get_next_cron_tick,
    is_valid_cron_string,
)


@beta
def build_last_update_freshness_checks(
    *,
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
    lower_bound_delta: datetime.timedelta,
    deadline_cron: Optional[str] = None,
    timezone: str = DEFAULT_FRESHNESS_TIMEZONE,
    severity: AssetCheckSeverity = DEFAULT_FRESHNESS_SEVERITY,
) -> Sequence[AssetChecksDefinition]:
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
        Sequence[AssetChecksDefinition]: `AssetChecksDefinition` objects which execute freshness checks
            for the provided assets.
    """
    check.inst_param(lower_bound_delta, "lower_bound_delta", datetime.timedelta)
    check.str_param(timezone, "timezone")
    check.opt_str_param(deadline_cron, "deadline_cron")
    check.invariant(
        deadline_cron is None or is_valid_cron_string(deadline_cron), "Invalid cron string."
    )
    check.inst_param(severity, "severity", AssetCheckSeverity)
    check.sequence_param(assets, "assets")
    ensure_no_duplicate_assets(assets)
    return [
        _build_freshness_multi_check(
            asset_keys=assets_to_keys(assets),
            deadline_cron=deadline_cron,
            timezone=timezone,
            severity=severity,
            lower_bound_delta=lower_bound_delta,
        )
    ]


def _build_freshness_multi_check(
    asset_keys: Sequence[AssetKey],
    deadline_cron: Optional[str],
    timezone: str,
    severity: AssetCheckSeverity,
    lower_bound_delta: datetime.timedelta,
) -> AssetChecksDefinition:
    params_metadata: dict[str, Any] = {
        TIMEZONE_PARAM_KEY: timezone,
        LOWER_BOUND_DELTA_PARAM_KEY: lower_bound_delta.total_seconds(),
    }
    if deadline_cron:
        params_metadata[DEADLINE_CRON_PARAM_KEY] = deadline_cron

    @freshness_multi_asset_check(
        params_metadata=JsonMetadataValue(params_metadata), asset_keys=asset_keys
    )
    def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
        for check_key in context.selected_asset_check_keys:
            asset_key = check_key.asset_key
            current_timestamp = get_current_timestamp()

            current_time_in_freshness_tz = datetime.datetime.fromtimestamp(
                current_timestamp, tz=get_timezone(timezone)
            )
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

            last_update_time_lower_bound = cast(datetime.datetime, deadline - lower_bound_delta)

            latest_record = retrieve_last_update_record(
                instance=context.instance, asset_key=asset_key, partition_key=None
            )
            update_timestamp = (
                retrieve_timestamp_from_record(latest_record) if latest_record else None
            )
            passed = (
                update_timestamp is not None
                and update_timestamp >= last_update_time_lower_bound.timestamp()
            )

            metadata: dict[str, MetadataValue] = {
                FRESHNESS_PARAMS_METADATA_KEY: JsonMetadataValue(params_metadata),
                LOWER_BOUND_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(
                    last_update_time_lower_bound.timestamp()
                ),
            }
            if latest_completed_cron_tick:
                metadata[LATEST_CRON_TICK_METADATA_KEY] = TimestampMetadataValue(
                    latest_completed_cron_tick.timestamp()
                )
            if passed:
                # If the asset is fresh, we can determine when it has the possibility of becoming stale again.
                # In the case of a deadline cron, this is the next cron tick after the current time.
                # In the case of just a lower_bound_delta, this is the last update time plus the
                # lower_bound_delta.
                fresh_until = (
                    get_next_cron_tick(
                        deadline_cron, current_time_in_freshness_tz, timezone
                    ).timestamp()
                    if deadline_cron
                    else check.not_none(update_timestamp) + lower_bound_delta.total_seconds()
                )
                metadata[FRESH_UNTIL_METADATA_KEY] = TimestampMetadataValue(fresh_until)
            if update_timestamp:
                metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY] = TimestampMetadataValue(
                    update_timestamp
                )

            yield AssetCheckResult(
                passed=passed,
                description=construct_description(
                    passed,
                    last_update_time_lower_bound=last_update_time_lower_bound.timestamp(),
                    current_timestamp=current_timestamp,
                    update_timestamp=update_timestamp,
                ),
                severity=severity,
                asset_key=asset_key,
                metadata=metadata,
            )

    return the_check


def construct_description(
    passed: bool,
    last_update_time_lower_bound: Optional[float],
    current_timestamp: float,
    update_timestamp: Optional[float],
) -> str:
    check.invariant(
        (passed and update_timestamp is not None) or not passed,
        "Should not be possible for check to pass without an update to the asset.",
    )

    allowed_delta = (
        seconds_in_words(current_timestamp - last_update_time_lower_bound)
        if last_update_time_lower_bound
        else None
    )
    actual_delta = (
        seconds_in_words(current_timestamp - update_timestamp) if update_timestamp else None
    )

    if passed:
        return f"Asset is currently fresh. The last update was {actual_delta} ago, within the allowed time range of {allowed_delta}."
    elif update_timestamp is None:
        return "Asset has never been observed/materialized."
    else:
        return (
            f"Asset is overdue for an update. The last update was {actual_delta} ago, "
            f"which is past the allowed distance of {allowed_delta} ago."
        )
