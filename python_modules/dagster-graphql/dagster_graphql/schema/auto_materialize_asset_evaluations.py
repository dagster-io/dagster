from collections.abc import Sequence
from typing import Optional

import graphene
from dagster._core.definitions.auto_materialize_rule_evaluation import AutoMaterializeDecisionType
from dagster._core.definitions.declarative_automation.legacy.rule_condition import RuleCondition
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetSubsetWithMetadata,
    AutomationConditionEvaluation,
)
from dagster._core.definitions.metadata import DagsterAssetMetadataValue
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.schema.auto_materialize_policy import GrapheneAutoMaterializeRule
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.partition_keys import (
    GraphenePartitionKeys,
    GraphenePartitionKeysOrError,
)
from dagster_graphql.schema.util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GrapheneTextRuleEvaluationData(graphene.ObjectType):
    text = graphene.String()

    class Meta:
        name = "TextRuleEvaluationData"


class GrapheneParentMaterializedRuleEvaluationData(graphene.ObjectType):
    updatedAssetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))
    willUpdateAssetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))

    class Meta:
        name = "ParentMaterializedRuleEvaluationData"


class GrapheneWaitingOnKeysRuleEvaluationData(graphene.ObjectType):
    waitingOnAssetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))

    class Meta:
        name = "WaitingOnKeysRuleEvaluationData"


class GrapheneAutoMaterializeRuleEvaluationData(graphene.Union):
    class Meta:
        types = (
            GrapheneTextRuleEvaluationData,
            GrapheneParentMaterializedRuleEvaluationData,
            GrapheneWaitingOnKeysRuleEvaluationData,
        )
        name = "AutoMaterializeRuleEvaluationData"


class GrapheneAutoMaterializeRuleEvaluation(graphene.ObjectType):
    partitionKeysOrError = graphene.Field(GraphenePartitionKeysOrError)
    evaluationData = graphene.Field(GrapheneAutoMaterializeRuleEvaluationData)

    class Meta:
        name = "AutoMaterializeRuleEvaluation"


class GrapheneAutoMaterializeRuleWithRuleEvaluations(graphene.ObjectType):
    rule = graphene.NonNull(GrapheneAutoMaterializeRule)
    ruleEvaluations = non_null_list(GrapheneAutoMaterializeRuleEvaluation)

    class Meta:
        name = "AutoMaterializeRuleWithRuleEvaluations"

    def __init__(
        self,
        rule: GrapheneAutoMaterializeRule,
        ruleEvaluations,
    ):
        super().__init__(
            rule=rule,
            ruleEvaluations=ruleEvaluations,
        )


def create_graphene_auto_materialize_rule_evaluation(
    asset_subset_with_metadata: AssetSubsetWithMetadata,
) -> Optional[GrapheneAutoMaterializeRuleEvaluation]:
    if not asset_subset_with_metadata.subset.is_partitioned:
        partition_keys_or_error = None
    else:
        partition_keys_or_error = GraphenePartitionKeys(
            partitionKeys=asset_subset_with_metadata.subset.subset_value.get_partition_keys()
        )

    metadata = asset_subset_with_metadata.metadata
    if "text" in metadata.keys() and isinstance(metadata["text"], str):
        rule_evaluation_data = GrapheneTextRuleEvaluationData(text=metadata["text"])
    elif any(key.startswith("updated_parent") for key in metadata.keys()):
        updatedAssetKeys = [
            value.asset_key
            for key, value in sorted(metadata.items())
            if key.startswith("updated_parent") and isinstance(value, DagsterAssetMetadataValue)
        ]
        willUpdateAssetKeys = [
            value.asset_key
            for key, value in sorted(metadata.items())
            if key.startswith("will_update_parent") and isinstance(value, DagsterAssetMetadataValue)
        ]
        rule_evaluation_data = GrapheneParentMaterializedRuleEvaluationData(
            updatedAssetKeys=updatedAssetKeys, willUpdateAssetKeys=willUpdateAssetKeys
        )
    elif any(key.startswith("waiting_on_ancestor") for key in metadata.keys()):
        waitingOnAssetKeys = [
            value.asset_key
            for key, value in sorted(metadata.items())
            if key.startswith("waiting_on_ancestor")
            and isinstance(value, DagsterAssetMetadataValue)
        ]
        rule_evaluation_data = GrapheneWaitingOnKeysRuleEvaluationData(
            waitingOnAssetKeys=waitingOnAssetKeys
        )
    else:
        rule_evaluation_data = None

    return GrapheneAutoMaterializeRuleEvaluation(
        partitionKeysOrError=partition_keys_or_error, evaluationData=rule_evaluation_data
    )


def _create_rules_with_rule_evaluations_for_decision_type(
    evaluation: AutomationConditionEvaluation, decision_type: AutoMaterializeDecisionType
) -> tuple[
    Sequence[GrapheneAutoMaterializeRule], Sequence[GrapheneAutoMaterializeRuleWithRuleEvaluations]
]:
    rules = []
    rules_with_rule_evaluations = []
    leaf_evaluations = evaluation.child_evaluations
    for le in leaf_evaluations:
        snapshot = le.condition_snapshot
        if snapshot.class_name != RuleCondition.__name__:
            continue
        rule = GrapheneAutoMaterializeRule(snapshot.description, decision_type)
        rules.append(rule)
        if le.subsets_with_metadata:
            rules_with_rule_evaluations.append(
                GrapheneAutoMaterializeRuleWithRuleEvaluations(
                    rule=rule,
                    ruleEvaluations=[
                        create_graphene_auto_materialize_rule_evaluation(sswm)
                        for sswm in le.subsets_with_metadata
                    ],
                )
            )
        elif le.true_subset.size > 0:
            rules_with_rule_evaluations.append(
                GrapheneAutoMaterializeRuleWithRuleEvaluations(
                    rule=rule,
                    ruleEvaluations=[
                        GrapheneAutoMaterializeRuleEvaluation(
                            partitionKeysOrError=GraphenePartitionKeys(
                                partitionKeys=le.true_subset.subset_value.get_partition_keys()
                            )
                            if le.true_subset.is_partitioned
                            else None,
                            evaluationData=None,
                        )
                    ],
                )
            )
    return rules, rules_with_rule_evaluations


def create_graphene_auto_materialize_rules_with_rule_evaluations(
    evaluation: AutomationConditionEvaluation,
) -> tuple[
    Sequence[GrapheneAutoMaterializeRule], Sequence[GrapheneAutoMaterializeRuleWithRuleEvaluations]
]:
    rules, rules_with_rule_evaluations = [], []

    if len(evaluation.child_evaluations) > 0:
        materialize_evaluation = evaluation.child_evaluations[0]
        rs, rwres = _create_rules_with_rule_evaluations_for_decision_type(
            materialize_evaluation, AutoMaterializeDecisionType.MATERIALIZE
        )
        rules.extend(rs)
        rules_with_rule_evaluations.extend(rwres)

    if (
        len(evaluation.child_evaluations) > 1
        and len(evaluation.child_evaluations[1].child_evaluations) == 1
    ):
        skip_evaluation = evaluation.child_evaluations[1].child_evaluations[0]
        rs, rwres = _create_rules_with_rule_evaluations_for_decision_type(
            skip_evaluation, AutoMaterializeDecisionType.SKIP
        )
        rules.extend(rs)
        rules_with_rule_evaluations.extend(rwres)

    if (
        len(evaluation.child_evaluations) > 2
        and len(evaluation.child_evaluations[2].child_evaluations) == 1
    ):
        discard_evaluation = evaluation.child_evaluations[2]
        rs, rwres = _create_rules_with_rule_evaluations_for_decision_type(
            discard_evaluation, AutoMaterializeDecisionType.DISCARD
        )
        rules.extend(rs)
        rules_with_rule_evaluations.extend(rwres)

    return rules, rules_with_rule_evaluations


class GrapheneAutoMaterializeAssetEvaluationRecord(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    evaluationId = graphene.NonNull(graphene.ID)
    numRequested = graphene.NonNull(graphene.Int)
    numSkipped = graphene.NonNull(graphene.Int)
    numDiscarded = graphene.NonNull(graphene.Int)
    rulesWithRuleEvaluations = non_null_list(GrapheneAutoMaterializeRuleWithRuleEvaluations)
    timestamp = graphene.NonNull(graphene.Float)
    runIds = non_null_list(graphene.String)
    rules = graphene.Field(graphene.List(graphene.NonNull(GrapheneAutoMaterializeRule)))
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        name = "AutoMaterializeAssetEvaluationRecord"

    def __init__(self, record: AutoMaterializeAssetEvaluationRecord):
        evaluation_with_run_ids = record.get_evaluation_with_run_ids()
        evaluation = evaluation_with_run_ids.evaluation
        (
            rules,
            rules_with_rule_evaluations,
        ) = create_graphene_auto_materialize_rules_with_rule_evaluations(evaluation)
        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            numRequested=evaluation_with_run_ids.evaluation.true_subset.size,
            numSkipped=0,
            numDiscarded=0,
            rulesWithRuleEvaluations=rules_with_rule_evaluations,
            timestamp=record.timestamp,
            runIds=evaluation_with_run_ids.run_ids,
            rules=sorted(rules, key=lambda rule: rule.className),
            assetKey=GrapheneAssetKey(path=record.key.path),
        )


class GrapheneAutoMaterializeAssetEvaluationRecords(graphene.ObjectType):
    records = non_null_list(GrapheneAutoMaterializeAssetEvaluationRecord)

    class Meta:
        name = "AutoMaterializeAssetEvaluationRecords"


class GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "AutoMaterializeAssetEvaluationNeedsMigrationError"


class GrapheneAutoMaterializeAssetEvaluationRecordsOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneAutoMaterializeAssetEvaluationRecords,
            GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
        )
        name = "AutoMaterializeAssetEvaluationRecordsOrError"
