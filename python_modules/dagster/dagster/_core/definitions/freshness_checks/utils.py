import datetime
from typing import Iterator, Optional, Sequence, Union, cast

from dagster import _check as check
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.event_api import AssetRecordsFilter, EventLogRecord
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import AssetCheckExecutionContext
from dagster._core.instance import DagsterInstance
from dagster._utils.security import non_secure_md5_hash_str

from ..assets import AssetsDefinition, SourceAsset
from ..events import AssetKey, CoercibleToAssetKey

# Constants
DEFAULT_FRESHNESS_SEVERITY = AssetCheckSeverity.WARN
DEFAULT_FRESHNESS_TIMEZONE = "UTC"

# Top-level metadata keys
LAST_UPDATED_TIMESTAMP_METADATA_KEY = "dagster/last_updated_timestamp"
FRESHNESS_PARAMS_METADATA_KEY = "dagster/freshness_params"
# When an asset is overdue, this represents the timestamp by which the asset was expected to arrive.
EXPECTED_BY_TIMESTAMP_METADATA_KEY = "dagster/expected_by_timestamp"
# When an asset is fresh, this represents the timestamp when the asset can become stale again.
FRESH_UNTIL_METADATA_KEY = "dagster/fresh_until_timestamp"
OVERDUE_SECONDS_METADATA_KEY = "dagster/overdue_seconds"

# dagster/freshness_params inner keys
LOWER_BOUND_DELTA_PARAM_KEY = "lower_bound_delta"
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
    asset_keys = [
        asset_key for asset in assets for asset_key in list(asset_to_keys_iterable(asset))
    ]
    duplicate_assets = [asset_key for asset_key in asset_keys if asset_keys.count(asset_key) > 1]
    check.invariant(
        len(duplicate_assets) == 0,
        f"Found duplicate assets in the provided list of assets: {duplicate_assets}. Please ensure that each asset is unique.",
    )


def asset_to_keys_iterable(
    asset: Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset],
) -> Iterator[AssetKey]:
    """Converts the provided asset construct to a sequence of AssetKeys.

    Args:
        asset (Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]): The asset to convert to a sequence of AssetKeys.

    Returns:
        Sequence[AssetKey]: A sequence of AssetKeys.
    """
    if isinstance(asset, AssetsDefinition):
        yield from asset.keys
    elif isinstance(asset, SourceAsset):
        yield asset.key
    else:
        yield AssetKey.from_coercible_or_definition(asset)


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


def retrieve_latest_record(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partition_key: Optional[str],
) -> Optional[EventLogRecord]:
    """Retrieve the latest materialization or observation record for the given asset.

    If the asset is partitioned, the latest record for the latest partition will be returned.
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
        return max(
            materializations.records[0],
            observations.records[0],
            key=lambda record: retrieve_timestamp_from_record(record),
        )
    else:
        return (
            materializations.records[0]
            if materializations.records
            else observations.records[0]
            if observations.records
            else None
        )


def retrieve_timestamp_from_record(asset_record: EventLogRecord) -> float:
    """Retrieve the timestamp from the given materialization or observation record."""
    check.inst_param(asset_record, "asset_record", EventLogRecord)
    if asset_record.event_log_entry.dagster_event_type == DagsterEventType.ASSET_MATERIALIZATION:
        return asset_record.timestamp
    else:
        metadata = check.not_none(asset_record.asset_observation).metadata
        value = metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY].value
        check.invariant(
            isinstance(value, float),
            f"Unexpected metadata value type for '{LAST_UPDATED_TIMESTAMP_METADATA_KEY}': "
            f"{type(metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY])}",
        )
        return cast(float, value)


def get_last_updated_timestamp(
    record: Optional[EventLogRecord], context: AssetCheckExecutionContext
) -> Optional[float]:
    if record is None:
        return None
    if record.asset_materialization is not None:
        return record.timestamp
    elif record.asset_observation is not None:
        metadata_value = record.asset_observation.metadata.get("dagster/last_updated_timestamp")
        if metadata_value is not None:
            return check.float_param(metadata_value.value, "last_updated_timestamp")
        else:
            context.log.warning(
                f"Could not find last updated timestamp in observation record for asset key "
                f"{check.not_none(record.asset_key).to_user_string()}. Please set "
                "dagster/last_updated_timestamp in the metadata of the observation record on "
                "assets which have freshness checks."
            )
            return None
    else:
        check.failed("Expected record to be an observation or materialization")


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


def unique_id_from_asset_keys(asset_keys: Sequence[AssetKey]) -> str:
    """Generate a unique ID from the provided asset keys.

    This is necessary to disambiguate between different ops underlying freshness checks without
    forcing the user to provide a name for the underlying op.
    """
    sorted_asset_keys = sorted(asset_keys, key=lambda asset_key: asset_key.to_string())
    return non_secure_md5_hash_str(
        ",".join([str(asset_key) for asset_key in sorted_asset_keys]).encode()
    )[:8]
