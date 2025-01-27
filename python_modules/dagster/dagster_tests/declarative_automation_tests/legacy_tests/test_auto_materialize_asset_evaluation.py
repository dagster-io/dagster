from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluationWithRunIds,
)
from dagster._serdes.serdes import deserialize_value


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
    deserialized_with_run_ids = deserialize_value(
        serialized_asset_evaluation, as_type=AutomationConditionEvaluationWithRunIds
    )
    deserialized = deserialized_with_run_ids.evaluation

    # we now deserialize these into empty evaluations
    assert deserialized.true_subset.size == 0
    assert len(deserialized.child_evaluations) == 0


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
    deserialized_with_run_ids = deserialize_value(
        serialized_asset_evaluation, as_type=AutomationConditionEvaluationWithRunIds
    )
    deserialized = deserialized_with_run_ids.evaluation

    # we now deserialize these into empty evaluations
    assert deserialized.true_subset.size == 0
    assert len(deserialized.child_evaluations) == 0
