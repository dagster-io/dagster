from datetime import datetime, timezone

from dagster import EventMetadataEntry, Output, check
from dagster.core.asset_defs import asset


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


def _id_range_for_time(start, end, hn_client):
    check.invariant(end >= start, "End time comes before start time")

    start = datetime.timestamp(
        datetime.strptime(start, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    )
    end = datetime.timestamp(
        datetime.strptime(end, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    )

    def _get_item_timestamp(item_id):
        item = hn_client.fetch_item_by_id(item_id)
        return item["time"]

    max_item_id = hn_client.fetch_max_item_id()

    # declared by resource to allow testability against snapshot
    min_item_id = hn_client.min_item_id()

    start_id = binary_search_nearest_left(_get_item_timestamp, min_item_id, max_item_id, start)
    end_id = binary_search_nearest_right(_get_item_timestamp, min_item_id, max_item_id, end)

    start_timestamp = str(datetime.fromtimestamp(_get_item_timestamp(start_id), tz=timezone.utc))
    end_timestamp = str(datetime.fromtimestamp(_get_item_timestamp(end_id), tz=timezone.utc))

    metadata_entries = [
        EventMetadataEntry.int(value=max_item_id, label="max_item_id"),
        EventMetadataEntry.int(value=start_id, label="start_id"),
        EventMetadataEntry.int(value=end_id, label="end_id"),
        EventMetadataEntry.int(value=end_id - start_id, label="items"),
        EventMetadataEntry.text(text=start_timestamp, label="start_timestamp"),
        EventMetadataEntry.text(text=end_timestamp, label="end_timestamp"),
    ]

    id_range = (start_id, end_id)
    return id_range, metadata_entries


@asset(
    required_resource_keys={"hn_client", "partition_start", "partition_end"},
    description="The lower (inclusive) and upper (exclusive) ids that bound the range for the partition",
)
def id_range_for_time(context):
    """
    For the configured time partition, searches for the range of ids that were created in that time.
    """
    id_range, metadata_entries = _id_range_for_time(
        context.resources.partition_start,
        context.resources.partition_end,
        context.resources.hn_client,
    )
    yield Output(id_range, metadata_entries=metadata_entries)
