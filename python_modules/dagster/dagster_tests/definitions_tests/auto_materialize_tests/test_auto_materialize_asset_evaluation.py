from dagster import MetadataValue
from dagster._core.definitions.asset_condition import (
    AssetConditionEvaluationWithRunIds,
    AssetSubsetWithMetadata,
)
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKey
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
        serialized_asset_evaluation, AssetConditionEvaluationWithRunIds
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
    deserialized_with_run_ids = deserialize_value(
        serialized_asset_evaluation, AssetConditionEvaluationWithRunIds
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


def test_backcompat_partitioned_asset() -> None:
    serialized_asset_evaluation = (
        '{"__class__": "AutoMaterializeAssetEvaluation", "asset_key": {"__class__": "AssetKey",'
        ' "path": ["B"]}, "num_discarded": 1, "num_requested": 1, "num_skipped": 1, '
        '"partition_subsets_by_condition": [[{"__class__": "AutoMaterializeRuleEvaluation", '
        '"evaluation_data": {"__class__": "ParentUpdatedRuleEvaluationData", "updated_asset_keys": '
        '{"__frozenset__": [{"__class__": "AssetKey", "path": ["A"]}]}, "will_update_asset_keys": '
        '{"__frozenset__": []}}, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed '
        'since latest materialization"}}, {"__class__": "SerializedPartitionsSubset", '
        '"serialized_partitions_def_class_name": "DailyPartitionsDefinition", '
        '"serialized_partitions_def_unique_id": "809725ad60ffac0302d5c81f6e45865e21ec0b85", '
        '"serialized_subset": "{\\"version\\": 1, \\"time_windows\\": [[1357344000.0, 1357603200.0]], '
        '\\"num_partitions\\": 3}"}], [{"__class__": "AutoMaterializeRuleEvaluation", '
        '"evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "MaterializeOnMissingRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "materialization is missing"}}, '
        '{"__class__": "SerializedPartitionsSubset", "serialized_partitions_def_class_name": '
        '"DailyPartitionsDefinition", "serialized_partitions_def_unique_id": '
        '"809725ad60ffac0302d5c81f6e45865e21ec0b85", "serialized_subset": '
        '"{\\"version\\": 1, \\"time_windows\\": [[1357344000.0, 1357603200.0]], \\"num_partitions\\": 3}"}], '
        '[{"__class__": "AutoMaterializeRuleEvaluation", "evaluation_data": {"__class__": '
        '"WaitingOnAssetsRuleEvaluationData", "waiting_on_asset_keys": {"__frozenset__": '
        '[{"__class__": "AssetKey", "path": ["A"]}]}}, "rule_snapshot": {"__class__": '
        '"AutoMaterializeRuleSnapshot", "class_name": "SkipOnParentMissingRule", "decision_type": '
        '{"__enum__": "AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data '
        'to be present"}}, {"__class__": "SerializedPartitionsSubset", '
        '"serialized_partitions_def_class_name": "DailyPartitionsDefinition", '
        '"serialized_partitions_def_unique_id": "809725ad60ffac0302d5c81f6e45865e21ec0b85", '
        '"serialized_subset": "{\\"version\\": 1, \\"time_windows\\": [[1357516800.0, 1357603200.0]], '
        '\\"num_partitions\\": 1}"}], [{"__class__": "AutoMaterializeRuleEvaluation", '
        '"evaluation_data": null, "rule_snapshot": {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "DiscardOnMaxMaterializationsExceededRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.DISCARD"}, "description": "exceeds 1 materialization(s) per '
        'minute"}}, {"__class__": "SerializedPartitionsSubset", '
        '"serialized_partitions_def_class_name": "DailyPartitionsDefinition", '
        '"serialized_partitions_def_unique_id": "809725ad60ffac0302d5c81f6e45865e21ec0b85", '
        '"serialized_subset": "{\\"version\\": 1, \\"time_windows\\": [[1357344000.0, 1357430400.0]], '
        '\\"num_partitions\\": 1}"}]], "rule_snapshots": [{"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "SkipOnBackfillInProgressRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "targeted by an in-progress backfill"'
        '}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": "MaterializeOnMissingRule", '
        '"decision_type": {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "description": '
        '"materialization is missing"}, {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "MaterializeOnRequiredForFreshnessRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "required to meet this or '
        'downstream asset\'s freshness policy"}, {"__class__": "AutoMaterializeRuleSnapshot", '
        '"class_name": "SkipOnParentOutdatedRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be up to '
        'date"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"SkipOnParentMissingRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "waiting on upstream data to be '
        'present"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"SkipOnRequiredButNonexistentParentsRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.SKIP"}, "description": "required parent partitions do not '
        'exist"}, {"__class__": "AutoMaterializeRuleSnapshot", "class_name": '
        '"MaterializeOnParentUpdatedRule", "decision_type": {"__enum__": '
        '"AutoMaterializeDecisionType.MATERIALIZE"}, "description": "upstream data has changed '
        'since latest materialization"}], "run_ids": {"__set__": []}}'
    )
    deserialized_with_run_ids = deserialize_value(
        serialized_asset_evaluation, AssetConditionEvaluationWithRunIds
    )
    deserialized = deserialized_with_run_ids.evaluation

    # all subsets should have zero size
    assert deserialized.true_subset.size == 0
    assert len(deserialized.child_evaluations) == 2
    (materialize_evaluation, not_skip_evaluation) = deserialized.child_evaluations
    assert materialize_evaluation.true_subset.size == 0
    assert not_skip_evaluation.true_subset.size == 0

    skip_evaluation = not_skip_evaluation.child_evaluations[0]
    assert skip_evaluation.true_subset.size == 0
    assert len(skip_evaluation.child_evaluations) == 4
    assert skip_evaluation.child_evaluations[0].true_subset.size == 0
