from dagster import PartitionsDefinition, StaticPartitionsDefinition
from dagster.core.asset_defs import asset
from dagster.core.asset_defs.asset_partitions import (
    PartitionKeyRange,
    get_downstream_partitions_for_partition_range,
    get_upstream_partitions_for_partition_range,
)
from dagster.core.asset_defs.partition_mapping import PartitionMapping
from dagster.core.definitions.events import AssetKey


def test_assets_with_same_partitioning():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @asset(partitions_def=partitions_def)
    def upstream_asset():
        pass

    @asset(partitions_def=partitions_def)
    def downstream_asset(upstream_asset):
        assert upstream_asset

    assert (
        get_upstream_partitions_for_partition_range(
            downstream_asset,
            upstream_asset,
            AssetKey("upstream_asset"),
            PartitionKeyRange("a", "c"),
        )
        == PartitionKeyRange("a", "c")
    )

    assert (
        get_downstream_partitions_for_partition_range(
            downstream_asset,
            upstream_asset,
            AssetKey("upstream_asset"),
            PartitionKeyRange("a", "c"),
        )
        == PartitionKeyRange("a", "c")
    )


def test_filter_mapping_partitions_dep():
    downstream_partitions = ["john", "ringo", "paul", "george"]
    upstream_partitions = [
        f"{hemisphere}|{beatle}"
        for beatle in downstream_partitions
        for hemisphere in ["southern", "northern"]
    ]
    downstream_partitions_def = StaticPartitionsDefinition(downstream_partitions)
    upstream_partitions_def = StaticPartitionsDefinition(upstream_partitions)

    class HemisphereFilteringPartitionMapping(PartitionMapping):
        def __init__(self, hemisphere: str):
            self.hemisphere = hemisphere

        def get_upstream_partitions_for_partition_range(
            self,
            downstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            return PartitionKeyRange(
                f"{self.hemisphere}|{downstream_partition_key_range.start}",
                f"{self.hemisphere}|{downstream_partition_key_range.end}",
            )

        def get_downstream_partitions_for_partition_range(
            self,
            upstream_partition_key_range: PartitionKeyRange,
            downstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
            upstream_partitions_def: PartitionsDefinition,  # pylint: disable=unused-argument
        ) -> PartitionKeyRange:
            return PartitionKeyRange(
                upstream_partition_key_range.start.split("|")[-1],
                upstream_partition_key_range.end.split("|")[-1],
            )

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset():
        pass

    @asset(
        partitions_def=downstream_partitions_def,
        partition_mappings={"upstream_asset": HemisphereFilteringPartitionMapping("southern")},
    )
    def downstream_asset(upstream_asset):
        assert upstream_asset

    assert (
        get_upstream_partitions_for_partition_range(
            downstream_asset,
            upstream_asset,
            AssetKey("upstream_asset"),
            PartitionKeyRange("ringo", "paul"),
        )
        == PartitionKeyRange("southern|ringo", "southern|paul")
    )

    assert (
        get_downstream_partitions_for_partition_range(
            downstream_asset,
            upstream_asset,
            AssetKey("upstream_asset"),
            PartitionKeyRange("southern|ringo", "southern|paul"),
        )
        == PartitionKeyRange("ringo", "paul")
    )
