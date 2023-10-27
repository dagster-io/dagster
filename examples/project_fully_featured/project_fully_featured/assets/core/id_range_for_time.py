from datetime import datetime, timezone
from typing import Any, Mapping, Tuple

from dagster import (
    OpExecutionContext,
    _check as check,
)

from project_fully_featured.resources.hn_resource import HNClient


def binary_search_nearest_left(get_value, start, end, min_target):
    mid = (start + end) // 2

    while start <= end:
        mid = (start + end) // 2
        mid_timestamp = get_value(mid)

        if mid_timestamp == min_target:
            return mid
        elif mid_timestamp < min_target:
            start = mid + 1
        elif mid_timestamp > min_target:
            end = mid - 1

    if mid == end:
        return end + 1

    return start


def binary_search_nearest_right(get_value, start, end, max_target):
    mid = (start + end) // 2

    while start <= end:
        mid = (start + end) // 2
        mid_timestamp = get_value(mid)

        if not mid_timestamp:
            end = end - 1

        if mid_timestamp == max_target:
            return mid
        elif mid_timestamp < max_target:
            start = mid + 1
        elif mid_timestamp > max_target:
            end = mid - 1

    if end == -1:
        return None

    if start > end:
        return end

    return end


def _id_range_for_time(start: int, end: int, hn_client: HNClient):
    check.invariant(end >= start, "End time comes before start time")

    def _get_item_timestamp(item_id):
        item = hn_client.fetch_item_by_id(item_id)
        if not item:
            raise ValueError(f"No item with id {item_id}")
        return item["time"]

    max_item_id = hn_client.fetch_max_item_id()

    # declared by resource to allow testability against snapshot
    min_item_id = hn_client.min_item_id()

    start_id = binary_search_nearest_left(_get_item_timestamp, min_item_id, max_item_id, start)
    end_id = binary_search_nearest_right(_get_item_timestamp, min_item_id, max_item_id, end)

    start_timestamp = str(datetime.fromtimestamp(_get_item_timestamp(start_id), tz=timezone.utc))
    end_timestamp = str(datetime.fromtimestamp(_get_item_timestamp(end_id), tz=timezone.utc))

    metadata = {
        "max_item_id": max_item_id,
        "start_id": start_id,
        "end_id": end_id,
        "items": end_id - start_id,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
    }

    id_range = (start_id, end_id)
    return id_range, metadata


def id_range_for_time(
    context: OpExecutionContext, hn_client: HNClient
) -> Tuple[Tuple[int, int], Mapping[str, Any]]:
    """For the configured time partition, searches for the range of ids that were created in that time."""
    start, end = context.asset_partitions_time_window_for_output()
    return _id_range_for_time(int(start.timestamp()), int(end.timestamp()), hn_client)
