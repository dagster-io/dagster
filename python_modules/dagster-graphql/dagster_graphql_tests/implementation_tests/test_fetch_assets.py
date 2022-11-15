from dagster import (
    DagsterInstance,
    asset,
    StaticPartitionsDefinition,
    materialize_to_memory,
    PartitionKeyRange,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster_graphql.implementation.fetch_assets import get_materialized_partition_ranges


def test_get_materialized_partition_ranges():
    instance = DagsterInstance.ephemeral()

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def asset1() -> None:
        ...

    asset_graph = AssetGraph.from_assets([asset1])

    assert (
        get_materialized_partition_ranges(
            asset_key=asset1.key, asset_graph=asset_graph, instance=instance
        )
        == []
    )

    materialize_to_memory([asset1], instance=instance, partition_key="a")

    assert get_materialized_partition_ranges(
        asset_key=asset1.key, asset_graph=asset_graph, instance=instance
    ) == [PartitionKeyRange("a", "a")]

    assert get_materialized_partition_ranges(
        asset_key=asset1.key, asset_graph=asset_graph, instance=instance
    ) == [PartitionKeyRange("a", "a")]

    materialize_to_memory([asset1], instance=instance, partition_key="a")

    assert get_materialized_partition_ranges(
        asset_key=asset1.key, asset_graph=asset_graph, instance=instance
    ) == [PartitionKeyRange("a", "a")]

    materialize_to_memory([asset1], instance=instance, partition_key="a")

    assert get_materialized_partition_ranges(
        asset_key=asset1.key, asset_graph=asset_graph, instance=instance
    ) == [PartitionKeyRange("a", "a"), PartitionKeyRange("b", "b")]


def test_get_materialized_partition_ranges_partitions_def_changes():
    ...
