from dagster import MetadataValue
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
)
from dagster._core.definitions.events import AssetKey


def test_backcompat_unpartitioned_skipped() -> None:
    serialized_asset_evaluation = (
        '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", '
        '"path": ["C"]}, "num_discarded": 0, "num_requested": 0, "num_skipped": 1, '
        '"partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", '
        '"evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "MaterializeOnCronRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "not materialized since last '
        'cron schedule tick of \'0 * * * *\' (timezone: UTC)"}}, null], [{"__class__": '
        '"AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": '
        '"WaitingOnAssetsRuleEvaluationData", "waiting_on_asset_keys": {"__frozenset__": '
        '[{"__class__": "AssetKey", "path": ["A"]}, {"__class__": "AssetKey", "path": ["B"]}]}}, '
        '"rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"SkipOnNotAllParentsUpdatedRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be '
        'updated"}}, null]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "SkipOnNotAllParentsUpdatedRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be '
        'updated"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"MaterializeOnCronRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "not materialized since last '
        'cron schedule tick of \'0 * * * *\' (timezone: UTC)"}], "run_ids": {"__set__": []}}'
    )
    deserialized_with_run_ids = (
        deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            serialized_asset_evaluation, None
        )
    )
    deserialized = deserialized_with_run_ids.evaluation

    assert deserialized.true_subset.size == 0
    assert len(deserialized.child_evaluations) == 2
    materialize_evaluation, not_skip_evaluation = deserialized.child_evaluations
    assert materialize_evaluation.true_subset.size == 1
    assert not_skip_evaluation.true_subset.size == 0
    skip_evaluation = not_skip_evaluation.child_evaluations[0]
    assert skip_evaluation.true_subset.size == 1
    assert len(skip_evaluation.child_evaluations) == 1
    assert skip_evaluation.child_evaluations[0].true_subset.size == 1
    assert len(skip_evaluation.child_evaluations[0].subsets_with_metadata) == 1
    skip_metadata = skip_evaluation.child_evaluations[0].subsets_with_metadata[0]
    assert skip_metadata == AssetSubsetWithMetadata(
        subset=AssetSubset(asset_key=AssetKey(["C"]), value=True),
        metadata={
            "waiting_on_ancestor_1": MetadataValue.asset(asset_key=AssetKey(["A"])),
            "waiting_on_ancestor_2": MetadataValue.asset(asset_key=AssetKey(["B"])),
        },
    )


def test_backcompat_unpartitioned_requested() -> None:
    serialized_asset_evaluation = (
        '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey", '
        '"path": ["C"]}, "num_discarded": 0, "num_requested": 1, "num_skipped": 0, '
        '"partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", '
        '"evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "MaterializeOnCronRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "not materialized since last '
        'cron schedule tick of \'0 * * * *\' (timezone: UTC)"}}, null]], "rule_snapshots": '
        '[{"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"SkipOnNotAllParentsUpdatedRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be '
        'updated"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"MaterializeOnCronRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "not materialized since last '
        'cron schedule tick of \'0 * * * *\' (timezone: UTC)"}], "run_ids": {"__set__": []}}'
    )
    deserialized_with_run_ids = (
        deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            serialized_asset_evaluation, None
        )
    )
    deserialized = deserialized_with_run_ids.evaluation
    assert len(deserialized.true_subset.asset_partitions) == 1
    assert len(deserialized.child_evaluations) == 2
    materialize_evaluation, not_skip_evaluation = deserialized.child_evaluations
    assert len(materialize_evaluation.child_evaluations) == 1
    cron_rule_evaluation = materialize_evaluation.child_evaluations[0]
    assert len(cron_rule_evaluation.child_evaluations) == 0
    assert cron_rule_evaluation.subsets_with_metadata == []
    assert len(not_skip_evaluation.child_evaluations) == 1
