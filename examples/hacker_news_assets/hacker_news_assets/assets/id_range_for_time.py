from datetime import datetime, timezone

from hacker_news_assets.partitions import hourly_partitions

from dagster import MetadataEntry, Output, asset, check


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


def _id_range_for_time(start: int, end: int, hn_client):
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

    metadata_entries = [
        MetadataEntry.int(value=max_item_id, label="max_item_id"),
        MetadataEntry.int(value=start_id, label="start_id"),
        MetadataEntry.int(value=end_id, label="end_id"),
        MetadataEntry.int(value=end_id - start_id, label="items"),
        MetadataEntry.text(text=start_timestamp, label="start_timestamp"),
        MetadataEntry.text(text=end_timestamp, label="end_timestamp"),
    ]

    id_range = (start_id, end_id)
    return id_range, metadata_entries


@asset(
    required_resource_keys={"hn_client"},
    description="The lower (inclusive) and upper (exclusive) ids that bound the range for the partition",
    partitions_def=hourly_partitions,
)
def id_range_for_time(context):
    """
    For the configured time partition, searches for the range of ids that were created in that time.
    """
    start, end = context.output_asset_partitions_time_window()
    id_range, metadata_entries = _id_range_for_time(
        start.timestamp(), end.timestamp(), context.resources.hn_client
    )
    yield Output(id_range, metadata_entries=metadata_entries)
