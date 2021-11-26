from dagster.core.definitions.events import AssetKey

from .asset import AssetsDefinition
from .partition_key_range import PartitionKeyRange


def get_parent_partitions(
    child_assets_def: AssetsDefinition,
    child_asset_key: AssetKey,
    parent_assets_def: AssetsDefinition,
    parent_asset_key: AssetKey,
    child_partition_key_range: PartitionKeyRange,
) -> PartitionKeyRange:
    """Returns the range of partition keys in the parent asset that include data necessary
    to compute the contents of the given partition key range in the child asset.
    """

    child_partition_mapping = child_assets_def.get_partition_mapping(parent_asset_key)
    return child_partition_mapping.get_parent_partitions(
        child_assets_def.partitions_def, parent_assets_def.partitions_def, child_partition_key_range
    )


def get_child_partitions(
    child_assets_def: AssetsDefinition,
    child_asset_key: AssetKey,
    parent_assets_def: AssetsDefinition,
    parent_asset_key: AssetKey,
    parent_partition_key_range: PartitionKeyRange,
) -> PartitionKeyRange:
    """Returns the range of partition keys in the child asset that use the data in the given
    partition key range of the child asset.
    """
    child_partition_mapping = child_assets_def.get_partition_mapping(parent_asset_key)
    return child_partition_mapping.get_child_partitions(
        child_assets_def.partitions_def,
        parent_assets_def.partitions_def,
        parent_partition_key_range,
    )
