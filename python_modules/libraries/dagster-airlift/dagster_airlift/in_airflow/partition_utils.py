from collections.abc import Mapping, Sequence
from datetime import (
    datetime,
    timezone as tz,
)
from enum import Enum
from typing import Any, NamedTuple, Optional

PARTITION_NAME_TAG = "dagster/partition"


class PartitionDefinitionType(Enum):
    TIME_WINDOW = "TIME_WINDOW"
    STATIC = "STATIC"
    MULTIPARTITIONED = "MULTIPARTITIONED"
    DYNAMIC = "DYNAMIC"


class TimeWindowPartitioningInformation(NamedTuple):
    fmt: str


class PartitioningInformation(NamedTuple):
    partitioning_type: PartitionDefinitionType
    partition_keys: Sequence[str]
    # Eventually we can add more of these for different partitioning types
    additional_info: Optional[TimeWindowPartitioningInformation]

    @staticmethod
    def from_asset_node_graphql(
        asset_nodes: Sequence[Mapping[str, Any]],
    ) -> Optional["PartitioningInformation"]:
        assets_partitioned = [_asset_is_partitioned(asset_node) for asset_node in asset_nodes]
        if any(assets_partitioned) and not all(assets_partitioned):
            raise Exception(
                "Found some unpartitioned assets and some partitioned assets in the same task. "
                "For a given task, all assets must have the same partitions definition. "
            )
        partition_keys_per_asset = [
            set(asset_node["partitionKeys"])
            for asset_node in asset_nodes
            if asset_node["isPartitioned"]
        ]
        if not all_sets_equal(partition_keys_per_asset):
            raise Exception(
                "Found differing partition keys across assets in this task. "
                "For a given task, all assets must have the same partitions definition. "
            )
        # Now we can proceed with the assumption that all assets are partitioned and have the same partition keys.
        # This, we only look at the first asset node.
        asset_node = next(iter(asset_nodes))
        if not asset_node["isPartitioned"]:
            return None
        partitioning_type = PartitionDefinitionType(asset_node["partitionDefinition"]["type"])
        return PartitioningInformation(
            partitioning_type=partitioning_type,
            partition_keys=asset_node["partitionKeys"],
            additional_info=_build_additional_info_for_type(asset_node, partitioning_type),
        )

    @property
    def time_window_partitioning_info(self) -> TimeWindowPartitioningInformation:
        if self.partitioning_type != PartitionDefinitionType.TIME_WINDOW:
            raise Exception(
                f"Partitioning type is {self.partitioning_type}, but expected {PartitionDefinitionType.TIME_WINDOW}"
            )
        if self.additional_info is None:
            raise Exception(
                f"Partitioning type is {self.partitioning_type}, but no additional info was provided."
            )
        return self.additional_info


def _build_additional_info_for_type(
    asset_node: Mapping[str, Any], partitioning_type: PartitionDefinitionType
) -> Optional[TimeWindowPartitioningInformation]:
    if partitioning_type != PartitionDefinitionType.TIME_WINDOW:
        return None
    return TimeWindowPartitioningInformation(fmt=asset_node["partitionDefinition"]["fmt"])


def all_sets_equal(list_of_sets):
    if not list_of_sets:
        return True
    return len(set.union(*list_of_sets)) == len(set.intersection(*list_of_sets))


def translate_logical_date_to_partition_key(
    logical_date: datetime, partitioning_info: PartitioningInformation
) -> str:
    if not partitioning_info.partitioning_type == PartitionDefinitionType.TIME_WINDOW:
        raise Exception(
            "Only time-window partitioned assets or non-partitioned assets are supported out of the box."
        )
    fmt = partitioning_info.time_window_partitioning_info.fmt
    partitions_and_datetimes = [
        (_get_partition_datetime(partition_key, fmt), partition_key)
        for partition_key in partitioning_info.partition_keys
    ]
    matching_partition = next(
        (
            partition_key
            for datetime, partition_key in partitions_and_datetimes
            if datetime.timestamp() == logical_date.timestamp()
        ),
        None,
    )
    if matching_partition is None:
        raise Exception(f"No partition key found for logical date {logical_date}")
    return matching_partition


def _asset_is_partitioned(asset_node: Mapping[str, Any]) -> bool:
    return asset_node["isPartitioned"]


def _get_partition_datetime(partition_key: str, fmt: str) -> datetime:
    try:
        return _add_default_utc_timezone_if_none(datetime.strptime(partition_key, fmt))
    except ValueError:
        raise Exception(f"Could not parse partition key {partition_key} with format {fmt}.")


def _add_default_utc_timezone_if_none(dt: datetime) -> datetime:
    return dt.replace(tzinfo=tz.utc) if dt.tzinfo is None else dt
