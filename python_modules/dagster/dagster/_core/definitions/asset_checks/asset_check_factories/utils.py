import datetime
from collections.abc import Iterator, Mapping, Sequence
from typing import Callable, Optional, Union

from dagster import _check as check
from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks.asset_check_spec import (
    AssetCheckKey,
    AssetCheckSeverity,
    AssetCheckSpec,
)
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.assets.definition.assets_definition import (
    AssetsDefinition,
    SourceAsset,
    unique_id_from_asset_and_check_keys,
)
from dagster._core.definitions.decorators.asset_check_decorator import (
    MultiAssetCheckFunction,
    multi_asset_check,
)
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.metadata import JsonMetadataValue
from dagster._core.definitions.metadata.metadata_value import TimestampMetadataValue
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance

# Constants
DEFAULT_FRESHNESS_SEVERITY = AssetCheckSeverity.WARN
DEFAULT_FRESHNESS_TIMEZONE = "UTC"

# Top-level metadata keys
LAST_UPDATED_TIMESTAMP_METADATA_KEY = "dagster/last_updated_timestamp"
FRESHNESS_PARAMS_METADATA_KEY = "dagster/freshness_params"
# The latest asset record should be no earlier than this timestamp.
LOWER_BOUND_TIMESTAMP_METADATA_KEY = "dagster/freshness_lower_bound_timestamp"
# When an asset is fresh, this represents the timestamp when the asset can become stale again.
FRESH_UNTIL_METADATA_KEY = "dagster/fresh_until_timestamp"
# If this is cron-based freshness, this is the latest tick of the cron.
LATEST_CRON_TICK_METADATA_KEY = "dagster/latest_cron_tick_timestamp"

# dagster/freshness_params inner keys
LOWER_BOUND_DELTA_PARAM_KEY = "lower_bound_delta_seconds"
DEADLINE_CRON_PARAM_KEY = "deadline_cron"
TIMEZONE_PARAM_KEY = "timezone"


def ensure_no_duplicate_assets(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
) -> None:
    """Finds duplicate assets in the provided list of assets, and errors if any are present.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]): The assets to check for duplicates.

    Returns:
        Sequence[AssetKey]: A list of the duplicate assets.
    """
    asset_keys = assets_to_keys(assets)
    duplicate_assets = [asset_key for asset_key in asset_keys if asset_keys.count(asset_key) > 1]
    check.invariant(
        len(duplicate_assets) == 0,
        f"Found duplicate assets in the provided list of assets: {duplicate_assets}. Please ensure that each asset is unique.",
    )


def asset_to_keys_iterable(
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
) -> Iterator[AssetKey]:
    if isinstance(asset, AssetsDefinition):
        yield from asset.keys
    elif isinstance(asset, SourceAsset):
        yield asset.key
    else:
        yield AssetKey.from_coercible_or_definition(asset)


def assets_to_keys(
    assets: Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]],
) -> Sequence[AssetKey]:
    """Converts the provided assets to a sequence of their contained AssetKeys."""
    return [asset_key for asset in assets for asset_key in asset_to_keys_iterable(asset)]


def ensure_no_duplicate_asset_checks(
    asset_checks: Sequence[AssetChecksDefinition],
) -> None:
    asset_check_keys = [
        asset_check_key
        for asset_check in asset_checks
        for asset_check_key in asset_check.check_keys
    ]
    duplicate_asset_checks = [
        asset_check_key
        for asset_check_key in asset_check_keys
        if asset_check_keys.count(asset_check_key) > 1
    ]
    check.invariant(
        len(duplicate_asset_checks) == 0,
        f"Found duplicate asset checks in the provided list of asset checks: {duplicate_asset_checks}. Please ensure that each provided asset check is unique.",
    )


def retrieve_last_update_record(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partition_key: Optional[str],
) -> Optional[EventLogRecord]:
    """Retrieve the latest materialization or observation record for the given asset.

    If the asset is partitioned, the latest record for the latest partition will be returned.

    There are a few weird edge cases to consider here:
        - Note that this may not be the latest record overall. We only look for the latest materialization
        and the latest observation, and return the latest of those two records that we
        can successfully parse. Take for example, the scenario where we have a materialization, and two
        obserations after that. If the latest observation is not parseable, we will return the materialization,
        even though there might be a more recent observation that we can parse. The reason we do
        this is to avoid an expensive query into the long-tail history of the asset. Retrieving the
        latest record of a particular type is cheap. Retrieving the latest N records is not.
        - If the asset has never been materialized and the latest observation is missing
        `dagster/last_updated_timestamp` metadata, we will return None.

    """
    materializations = instance.fetch_materializations(
        records_filter=AssetRecordsFilter(
            asset_key=asset_key, asset_partitions=[partition_key] if partition_key else None
        ),
        limit=1,
    )
    observations = instance.fetch_observations(
        records_filter=AssetRecordsFilter(
            asset_key=asset_key, asset_partitions=[partition_key] if partition_key else None
        ),
        limit=1,
    )
    if materializations.records and observations.records:
        mat_timestamp = retrieve_timestamp_from_record(materializations.records[0])
        obs_timestamp = retrieve_timestamp_from_record(observations.records[0])
        if not obs_timestamp:
            return materializations.records[0]
        if not mat_timestamp:
            return observations.records[0]
        return (
            materializations.records[0]
            if mat_timestamp > obs_timestamp
            else observations.records[0]
        )
    else:
        return (
            materializations.records[0]
            if materializations.records
            else observations.records[0]
            if observations.records
            else None
        )


def retrieve_timestamp_from_record(asset_record: EventLogRecord) -> Optional[float]:
    """Retrieve the timestamp from the given materialization or observation record."""
    check.inst_param(asset_record, "asset_record", EventLogRecord)
    default_value = None if asset_record.asset_observation else asset_record.timestamp
    return (
        get_timestamp_out_of_metadata_if_set(
            check.not_none(asset_record.asset_event).metadata, LAST_UPDATED_TIMESTAMP_METADATA_KEY
        )
        or default_value
    )


def get_timestamp_out_of_metadata_if_set(metadata: Mapping, key: str) -> Optional[float]:
    if key not in metadata:
        return None
    value = check.inst(
        metadata[key],
        TimestampMetadataValue,
        f"Expected {key} in asset metadat to be a TimestampMetadataValue.",
    )
    return value.value


def get_description_for_freshness_check_result(
    passed: bool,
    update_timestamp: Optional[float],
    last_update_time_lower_bound: datetime.datetime,
    current_timestamp: float,
    expected_partition_key: Optional[str],
    record_arrival_timestamp: Optional[float],
    event_type: Optional[DagsterEventType],
) -> str:
    check.invariant(
        (passed and update_timestamp is not None) or not passed,
        "Should not be possible for check to pass without an update to the asset.",
    )
    out_of_date_observation = record_arrival_timestamp is None or (
        record_arrival_timestamp < last_update_time_lower_bound.timestamp()
        and event_type == DagsterEventType.ASSET_OBSERVATION
    )
    update_time_delta_str = (
        seconds_in_words(current_timestamp - update_timestamp) if update_timestamp else None
    )
    last_update_time_lower_bound_delta_str = seconds_in_words(
        current_timestamp - last_update_time_lower_bound.timestamp()
    )
    return (
        f"Partition {expected_partition_key} is fresh. Expected the partition to arrive within the last {last_update_time_lower_bound_delta_str}, and it arrived {update_time_delta_str} ago."
        if passed and expected_partition_key
        else f"Partition {expected_partition_key} is overdue. Expected the partition to arrive within the last {last_update_time_lower_bound_delta_str}."
        if not passed
        and expected_partition_key  # Since we search for a specific partition, if that partition has never been materialized, we will have no record and is therefore in an "unknown" state, but we can't distinguish between that and an overdue state, so we call it overdue regardless.
        else f"Asset is fresh. Expected an update within the last {last_update_time_lower_bound_delta_str}, and found an update {update_time_delta_str} ago."
        if passed and update_timestamp
        else f"Asset is in an unknown state. Expected an update within the last {last_update_time_lower_bound_delta_str}, but we have not received an observation in that time, so we can't determine the state of the asset."
        if not passed and update_timestamp and out_of_date_observation
        else f"Asset is overdue. Expected an update within the last {last_update_time_lower_bound_delta_str}."
    )


def seconds_in_words(delta: float) -> str:
    """Converts the provided number of seconds to a human-readable string.

    Return format is "X days, Y hours, Z minutes, A seconds".
    """
    # Edge case: If the delta is 0 seconds exactly, we should return "0 seconds".
    if delta == 0:
        return "0 seconds"
    days = int(delta // 86400)
    days_unit = "days" if days > 1 else "day" if days == 1 else None
    hours = int(delta % 86400 // 3600)
    hours_unit = "hours" if hours > 1 else "hour" if hours == 1 else None
    minutes = int((delta % 3600) // 60)
    minutes_unit = "minutes" if minutes > 1 else "minute" if minutes == 1 else None
    seconds = int(delta % 60)
    seconds_unit = "seconds" if seconds > 1 else "second" if seconds == 1 else None
    return ", ".join(
        filter(
            None,
            [
                f"{days} {days_unit}" if days_unit else None,
                f"{hours} {hours_unit}" if hours_unit else None,
                f"{minutes} {minutes_unit}" if minutes_unit else None,
                f"{seconds} {seconds_unit}" if seconds_unit else None,
            ],
        )
    )


def freshness_multi_asset_check(
    params_metadata: JsonMetadataValue, asset_keys: Sequence[AssetKey], blocking: bool
):
    def inner(fn: MultiAssetCheckFunction) -> AssetChecksDefinition:
        return multi_asset_check(
            specs=[
                AssetCheckSpec(
                    "freshness_check",
                    asset=asset_key,
                    metadata={FRESHNESS_PARAMS_METADATA_KEY: params_metadata},
                    description="Evaluates freshness for targeted asset.",
                    blocking=blocking,
                )
                for asset_key in asset_keys
            ],
            can_subset=True,
            name=f"freshness_check_{unique_id_from_asset_and_check_keys(asset_keys)}",
        )(fn)

    return inner


def build_multi_asset_check(
    check_specs: Sequence[AssetCheckSpec],
    check_fn: Callable[[DagsterInstance, AssetCheckKey], tuple[bool, str]],
    severity: AssetCheckSeverity,
) -> Sequence[AssetChecksDefinition]:
    @multi_asset_check(
        specs=check_specs,
        can_subset=True,
        name=f"asset_check_{unique_id_from_asset_and_check_keys([spec.key for spec in check_specs])}",
    )
    def _checks(context):
        for asset_check_key in context.selected_asset_check_keys:
            passed, description = check_fn(context.instance, asset_check_key)
            yield AssetCheckResult(
                passed=passed,
                description=description,
                severity=severity,
                check_name=asset_check_key.name,
                asset_key=asset_check_key.asset_key,
            )

    return [_checks]
