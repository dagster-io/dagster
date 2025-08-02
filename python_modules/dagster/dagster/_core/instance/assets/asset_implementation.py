"""Asset domain implementation functions - extracted from DagsterInstance."""

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
    from dagster._core.event_api import EventRecordsResult
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance.assets.asset_instance_ops import AssetInstanceOps
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecord
    from dagster._core.storage.event_log.base import (
        AssetRecord,
        AssetRecordsFilter,
        PlannedMaterializationInfo,
    )
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue


def can_read_asset_status_cache(ops: "AssetInstanceOps") -> bool:
    """Check if asset status cache can be read - moved from DagsterInstance.can_read_asset_status_cache()."""
    return ops.event_log_storage.can_read_asset_status_cache()


def update_asset_cached_status_data(
    ops: "AssetInstanceOps", asset_key: "AssetKey", cache_values: "AssetStatusCacheValue"
) -> None:
    """Update asset cached status data - moved from DagsterInstance.update_asset_cached_status_data()."""
    ops.event_log_storage.update_asset_cached_status_data(asset_key, cache_values)


def wipe_asset_cached_status(ops: "AssetInstanceOps", asset_keys: Sequence["AssetKey"]) -> None:
    """Wipe asset cached status - moved from DagsterInstance.wipe_asset_cached_status()."""
    from dagster._core.definitions.asset_key import AssetKey

    check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
    for asset_key in asset_keys:
        ops.event_log_storage.wipe_asset_cached_status(asset_key)


def all_asset_keys(ops: "AssetInstanceOps") -> Sequence["AssetKey"]:
    """Get all asset keys - moved from DagsterInstance.all_asset_keys()."""
    return ops.event_log_storage.all_asset_keys()


def get_asset_keys(
    ops: "AssetInstanceOps",
    prefix: Optional[Sequence[str]] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> Sequence["AssetKey"]:
    """Return a filtered subset of asset keys managed by this instance.
    Moved from DagsterInstance.get_asset_keys().

    Args:
        prefix (Optional[Sequence[str]]): Return only assets having this key prefix.
        limit (Optional[int]): Maximum number of keys to return.
        cursor (Optional[str]): Cursor to use for pagination.

    Returns:
        Sequence[AssetKey]: List of asset keys.
    """
    return ops.event_log_storage.get_asset_keys(prefix=prefix, limit=limit, cursor=cursor)


def has_asset_key(ops: "AssetInstanceOps", asset_key: "AssetKey") -> bool:
    """Return true if this instance manages the given asset key.
    Moved from DagsterInstance.has_asset_key().

    Args:
        asset_key (AssetKey): Asset key to check.
    """
    return ops.event_log_storage.has_asset_key(asset_key)


def get_latest_materialization_events(
    ops: "AssetInstanceOps", asset_keys: Iterable["AssetKey"]
) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
    """Get latest materialization events - moved from DagsterInstance.get_latest_materialization_events()."""
    return ops.event_log_storage.get_latest_materialization_events(asset_keys)


def get_latest_materialization_event(
    ops: "AssetInstanceOps", asset_key: "AssetKey"
) -> Optional["EventLogEntry"]:
    """Fetch the latest materialization event for the given asset key.
    Moved from DagsterInstance.get_latest_materialization_event().

    Args:
        asset_key (AssetKey): Asset key to return materialization for.

    Returns:
        Optional[EventLogEntry]: The latest materialization event for the given asset
            key, or `None` if the asset has not been materialized.
    """
    return ops.event_log_storage.get_latest_materialization_events([asset_key]).get(asset_key)


def get_latest_asset_check_evaluation_record(
    ops: "AssetInstanceOps", asset_check_key: "AssetCheckKey"
) -> Optional["AssetCheckExecutionRecord"]:
    """Get latest asset check evaluation record - moved from DagsterInstance.get_latest_asset_check_evaluation_record()."""
    return ops.event_log_storage.get_latest_asset_check_execution_by_key([asset_check_key]).get(
        asset_check_key
    )


def fetch_materializations(
    ops: "AssetInstanceOps",
    records_filter: Union["AssetKey", "AssetRecordsFilter"],
    limit: int,
    cursor: Optional[str] = None,
    ascending: bool = False,
) -> "EventRecordsResult":
    """Return a list of materialization records stored in the event log storage.
    Moved from DagsterInstance.fetch_materializations().

    Args:
        records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
            filter event records.
        limit (int): Number of results to get.
        cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
        ascending (Optional[bool]): Sort the result in ascending order if True, descending
            otherwise. Defaults to descending.

    Returns:
        EventRecordsResult: Object containing a list of event log records and a cursor string.
    """
    return ops.event_log_storage.fetch_materializations(records_filter, limit, cursor, ascending)


def fetch_failed_materializations(
    ops: "AssetInstanceOps",
    records_filter: Union["AssetKey", "AssetRecordsFilter"],
    limit: int,
    cursor: Optional[str] = None,
    ascending: bool = False,
) -> "EventRecordsResult":
    """Return a list of AssetFailedToMaterialization records stored in the event log storage.
    Moved from DagsterInstance.fetch_failed_materializations().

    Args:
        records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
            filter event records.
        limit (int): Number of results to get.
        cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
        ascending (Optional[bool]): Sort the result in ascending order if True, descending
            otherwise. Defaults to descending.

    Returns:
        EventRecordsResult: Object containing a list of event log records and a cursor string.
    """
    return ops.event_log_storage.fetch_failed_materializations(
        records_filter, limit, cursor, ascending
    )


def wipe_assets(ops: "AssetInstanceOps", asset_keys: Sequence["AssetKey"]) -> None:
    """Wipes asset event history from the event log for the given asset keys.
    Moved from DagsterInstance.wipe_assets().

    Args:
        asset_keys (Sequence[AssetKey]): Asset keys to wipe.
    """
    from dagster._core.definitions.asset_key import AssetKey
    from dagster._core.events import AssetWipedData, DagsterEvent, DagsterEventType
    from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

    check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
    for asset_key in asset_keys:
        ops.event_log_storage.wipe_asset(asset_key)
        ops.report_dagster_event(
            run_id=RUNLESS_RUN_ID,
            dagster_event=DagsterEvent(
                event_type_value=DagsterEventType.ASSET_WIPED.value,
                event_specific_data=AssetWipedData(asset_key=asset_key, partition_keys=None),
                job_name=RUNLESS_JOB_NAME,
            ),
        )


def wipe_asset_partitions(
    ops: "AssetInstanceOps",
    asset_key: "AssetKey",
    partition_keys: Sequence[str],
) -> None:
    """Wipes asset event history from the event log for the given asset key and partition keys.
    Moved from DagsterInstance.wipe_asset_partitions().

    Args:
        asset_key (AssetKey): Asset key to wipe.
        partition_keys (Sequence[str]): Partition keys to wipe.
    """
    from dagster._core.events import AssetWipedData, DagsterEvent, DagsterEventType
    from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

    ops.event_log_storage.wipe_asset_partitions(asset_key, partition_keys)
    ops.report_dagster_event(
        run_id=RUNLESS_RUN_ID,
        dagster_event=DagsterEvent(
            event_type_value=DagsterEventType.ASSET_WIPED.value,
            event_specific_data=AssetWipedData(asset_key=asset_key, partition_keys=partition_keys),
            job_name=RUNLESS_JOB_NAME,
        ),
    )


def get_asset_records(
    ops: "AssetInstanceOps", asset_keys: Optional[Sequence["AssetKey"]] = None
) -> Sequence["AssetRecord"]:
    """Return an `AssetRecord` for each of the given asset keys.
    Moved from DagsterInstance.get_asset_records().

    Args:
        asset_keys (Optional[Iterable[AssetKey]]): List of asset keys to retrieve records for.

    Returns:
        Sequence[AssetRecord]: List of asset records.
    """
    return ops.event_log_storage.get_asset_records(asset_keys)


def get_event_tags_for_asset(
    ops: "AssetInstanceOps",
    asset_key: "AssetKey",
    filter_tags: Optional[Mapping[str, str]] = None,
    filter_event_id: Optional[int] = None,
) -> Sequence[Mapping[str, str]]:
    """Fetches asset event tags for the given asset key.
    Moved from DagsterInstance.get_event_tags_for_asset().

    If filter_tags is provided, searches for events containing all of the filter tags. Then,
    returns all tags for those events. This enables searching for multipartitioned asset
    partition tags with a fixed dimension value, e.g. all of the tags for events where
    "country" == "US".

    If filter_event_id is provided, searches for the event with the provided event_id.

    Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
    single event.
    """
    return ops.event_log_storage.get_event_tags_for_asset(asset_key, filter_tags, filter_event_id)


def get_latest_planned_materialization_info(
    ops: "AssetInstanceOps",
    asset_key: "AssetKey",
    partition: Optional[str] = None,
) -> Optional["PlannedMaterializationInfo"]:
    """Get latest planned materialization info.
    Moved from DagsterInstance.get_latest_planned_materialization_info().
    """
    return ops.event_log_storage.get_latest_planned_materialization_info(asset_key, partition)
