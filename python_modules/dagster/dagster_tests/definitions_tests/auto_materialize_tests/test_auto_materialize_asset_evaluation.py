from dagster import AssetKey, AutoMaterializePolicy, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeRule,
    AutoMaterializeRuleEvaluation,
    ParentUpdatedRuleEvaluationData,
    WaitingOnAssetsRuleEvaluationData,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._serdes.serdes import deserialize_value, serialize_value

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions, auto_materialize_policy=AutoMaterializePolicy.eager())
def my_asset(_):
    pass


def test_backcompat():
    serialized_asset_evaluation = (
        '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey",'
        ' "path": ["my_asset"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 2,'
        ' "partition_subsets_by_condition": [[{"__class__": "MissingAutoMaterializeCondition",'
        ' "decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}}, {"__class__":'
        ' "SerializedPartitionsSubset", "serialized_partitions_def_class_name":'
        ' "StaticPartitionsDefinition", "serialized_partitions_def_unique_id":'
        ' "411905f695e47a51ceafc178e6cd4eb3680f4453", "serialized_subset": "{\\"version\\": 1,'
        ' \\"subset\\": [\\"a\\", \\"b\\"]}"}], [{"__class__":'
        ' "ParentOutdatedAutoMaterializeCondition", "decision_type": {"__enum__":'
        ' "AutoMaterializeDecisionType.SKIP"}, "waiting_on_asset_keys": {"__frozenset__":'
        ' [{"__class__": "AssetKey", "path": ["parent1"]}, {"__class__": "AssetKey", "path":'
        ' ["parent2"]}]}}, {"__class__": "SerializedPartitionsSubset",'
        ' "serialized_partitions_def_class_name": "StaticPartitionsDefinition",'
        ' "serialized_partitions_def_unique_id": "411905f695e47a51ceafc178e6cd4eb3680f4453",'
        ' "serialized_subset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}], [{"__class__":'
        ' "ParentMaterializedAutoMaterializeCondition", "decision_type": {"__enum__":'
        ' "AutoMaterializeDecisionType.MATERIALIZE"}, "updated_asset_keys": {"__frozenset__":'
        ' [{"__class__": "AssetKey", "path": ["parent1"]}, {"__class__": "AssetKey", "path":'
        ' ["parent2"]}]}, "will_update_asset_keys": {"__frozenset__": [{"__class__": "AssetKey",'
        ' "path": ["parent3"]}]}}, {"__class__": "SerializedPartitionsSubset",'
        ' "serialized_partitions_def_class_name": "StaticPartitionsDefinition",'
        ' "serialized_partitions_def_unique_id": "411905f695e47a51ceafc178e6cd4eb3680f4453",'
        ' "serialized_subset": "{\\"version\\": 1, \\"subset\\": [\\"b\\"]}"}], [{"__class__":'
        ' "ParentOutdatedAutoMaterializeCondition", "decision_type": {"__enum__":'
        ' "AutoMaterializeDecisionType.SKIP"}, "waiting_on_asset_keys": {"__frozenset__":'
        ' [{"__class__": "AssetKey", "path": ["parent1"]}]}}, {"__class__":'
        ' "SerializedPartitionsSubset", "serialized_partitions_def_class_name":'
        ' "StaticPartitionsDefinition", "serialized_partitions_def_unique_id":'
        ' "411905f695e47a51ceafc178e6cd4eb3680f4453", "serialized_subset": "{\\"version\\": 1,'
        ' \\"subset\\": [\\"b\\"]}"}]], "run_ids": {"__set__": []}}'
    )
    expected_asset_evaluation = AutoMaterializeAssetEvaluation.from_rule_evaluation_results(
        asset_key=AssetKey(["my_asset"]),
        asset_graph=AssetGraph.from_assets([my_asset]),
        asset_partitions_by_rule_evaluation=[
            (
                AutoMaterializeRuleEvaluation(
                    rule_snapshot=AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                    evaluation_data=None,
                ),
                {AssetKeyPartitionKey(AssetKey(["my_asset"]), p) for p in ("a", "b")},
            ),
            (
                AutoMaterializeRuleEvaluation(
                    rule_snapshot=AutoMaterializeRule.materialize_on_parent_updated().to_snapshot(),
                    evaluation_data=ParentUpdatedRuleEvaluationData(
                        updated_asset_keys=frozenset(
                            {AssetKey(["parent1"]), AssetKey(["parent2"])}
                        ),
                        will_update_asset_keys=frozenset({AssetKey(["parent3"])}),
                    ),
                ),
                {AssetKeyPartitionKey(AssetKey(["my_asset"]), "b")},
            ),
            (
                AutoMaterializeRuleEvaluation(
                    rule_snapshot=AutoMaterializeRule.skip_on_parent_outdated().to_snapshot(),
                    evaluation_data=WaitingOnAssetsRuleEvaluationData(
                        waiting_on_asset_keys=frozenset(
                            {AssetKey(["parent1"]), AssetKey(["parent2"])}
                        ),
                    ),
                ),
                {AssetKeyPartitionKey(AssetKey(["my_asset"]), "a")},
            ),
            (
                AutoMaterializeRuleEvaluation(
                    rule_snapshot=AutoMaterializeRule.skip_on_parent_outdated().to_snapshot(),
                    evaluation_data=WaitingOnAssetsRuleEvaluationData(
                        waiting_on_asset_keys=frozenset({AssetKey(["parent1"])}),
                    ),
                ),
                {AssetKeyPartitionKey(AssetKey(["my_asset"]), "a")},
            ),
        ],
        num_requested=0,
        num_skipped=2,
        num_discarded=0,
        dynamic_partitions_store=None,
    )

    # Previously serialized asset evaluations do not contain rule snapshots, so
    # we override to be None
    expected_asset_evaluation = expected_asset_evaluation._replace(rule_snapshots=None)

    # json doesn't handle tuples, so they get turned into lists
    assert (
        deserialize_value(serialized_asset_evaluation)._replace(
            partition_subsets_by_condition=[
                tuple(t) for t in expected_asset_evaluation.partition_subsets_by_condition
            ]
        )
        == expected_asset_evaluation
    )
    assert (
        deserialize_value(serialize_value(expected_asset_evaluation))._replace(
            partition_subsets_by_condition=[
                tuple(t) for t in expected_asset_evaluation.partition_subsets_by_condition
            ]
        )
        == expected_asset_evaluation
    )
