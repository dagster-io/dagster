from dagster import AssetKey, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_reconciliation_sensor import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeCondition,
    AutoMaterializeReason,
    AutoMaterializeSkipCondition,
    AutoMaterializeSkipReason,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_num_requested():
    asset_graph = AssetGraph.from_assets([my_asset])

    e1 = AutoMaterializeAssetEvaluation.from_reasons(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        materialize_reasons={},
        skip_reasons={},
    )
    assert e1.num_requested == 0
    assert e1.num_skipped == 0
    assert e1.num_discarded == 0

    e2 = AutoMaterializeAssetEvaluation.from_reasons(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        materialize_reasons={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): AutoMaterializeReason(
                AutoMaterializeCondition.FRESHNESS
            )
        },
        skip_reasons={},
    )

    assert e2.num_requested == 1
    assert e2.num_skipped == 0

    e3 = AutoMaterializeAssetEvaluation.from_reasons(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        materialize_reasons={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): AutoMaterializeReason(
                AutoMaterializeCondition.FRESHNESS
            )
        },
        skip_reasons={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): AutoMaterializeSkipReason(
                AutoMaterializeSkipCondition.PARENT_OUTDATED
            )
        },
    )
    assert e3.num_requested == 0
    assert e3.num_skipped == 1

    e4 = AutoMaterializeAssetEvaluation.from_reasons(
        asset_graph=asset_graph,
        asset_key=AssetKey("my_asset"),
        materialize_reasons={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): AutoMaterializeReason(
                AutoMaterializeCondition.FRESHNESS
            ),
            AssetKeyPartitionKey(AssetKey("my_asset"), "b"): AutoMaterializeReason(
                AutoMaterializeCondition.FRESHNESS
            ),
        },
        skip_reasons={
            AssetKeyPartitionKey(AssetKey("my_asset"), "a"): AutoMaterializeSkipReason(
                AutoMaterializeSkipCondition.PARENT_OUTDATED
            )
        },
    )
    assert e4.num_requested == 1
    assert e4.num_skipped == 1
