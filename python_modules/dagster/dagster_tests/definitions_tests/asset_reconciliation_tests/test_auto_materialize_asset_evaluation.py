from dagster import AssetKey, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_reconciliation_sensor import AutoMaterializeAssetEvaluation
from dagster._core.definitions.auto_materialize_condition import (
    MissingAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_num_requested():
    asset_graph = AssetGraph.from_assets([my_asset])

    e1 = AutoMaterializeAssetEvaluation.from_conditions(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        conditions_by_asset_partition={},
        dynamic_partitions_store=None,
    )
    assert e1.num_requested == 0
    assert e1.num_skipped == 0
    assert e1.num_discarded == 0

    e2 = AutoMaterializeAssetEvaluation.from_conditions(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        conditions_by_asset_partition={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): {MissingAutoMaterializeCondition()}
        },
        dynamic_partitions_store=None,
    )

    assert e2.num_requested == 1
    assert e2.num_skipped == 0
    assert e2.num_discarded == 0

    e3 = AutoMaterializeAssetEvaluation.from_conditions(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        conditions_by_asset_partition={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): {
                MissingAutoMaterializeCondition(),
                ParentOutdatedAutoMaterializeCondition(),
            }
        },
        dynamic_partitions_store=None,
    )
    assert e3.num_requested == 0
    assert e3.num_skipped == 1
    assert e3.num_discarded == 0

    e4 = AutoMaterializeAssetEvaluation.from_conditions(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        conditions_by_asset_partition={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): {
                MissingAutoMaterializeCondition(),
                ParentOutdatedAutoMaterializeCondition(),
            },
            AssetKeyPartitionKey(AssetKey("my_asset"), "b"): {
                MissingAutoMaterializeCondition(),
            },
        },
        dynamic_partitions_store=None,
    )
    assert e4.num_requested == 1
    assert e4.num_skipped == 1
    assert e4.num_discarded == 0
