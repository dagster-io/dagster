from dagster import AssetKey, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule,
    AutoMaterializeAssetEvaluation,
    AutoMaterializeRuleEvaluation,
    MissingAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from dagster._core.definitions.events import AssetKeyPartitionKey

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_backcompat():
    pass
