import pytest
from dagster import (
    AssetMaterialization,
    DagsterInvalidDefinitionError,
    PartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster.core.asset_defs import asset, build_assets_job
from dagster.core.asset_defs.asset_partitions import (
    get_downstream_partitions_for_partition_range,
    get_upstream_partitions_for_partition_range,
)
from dagster.core.asset_defs.partition_mapping import PartitionMapping
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition_key_range import PartitionKeyRange


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


def test_single_partitioned_asset_job():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c", "d"])

    @asset(partitions_def=partitions_def)
    def my_asset():
        pass

    my_job = build_assets_job("my_job", assets=[my_asset])
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("my_asset") == [
        AssetMaterialization(asset_key=AssetKey(["my_asset"]), partition="b")
    ]


def test_two_partitioned_assets_job():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def upstream():
        pass

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
    def downstream(upstream):
        assert upstream is None

    my_job = build_assets_job("my_job", assets=[upstream, downstream])
    result = my_job.execute_in_process(partition_key="b")
    assert result.asset_materializations_for_node("upstream") == [
        AssetMaterialization(AssetKey(["upstream"]), partition="b")
    ]
    assert result.asset_materializations_for_node("downstream") == [
        AssetMaterialization(AssetKey(["downstream"]), partition="b")
    ]


def test_assets_job_with_different_partitions_defs():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
        def upstream():
            pass

        @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c", "d"]))
        def downstream(upstream):
            assert upstream is None

        build_assets_job("my_job", assets=[upstream, downstream])
