from collections import defaultdict
from typing import Optional, Sequence, Tuple

import dagster._check as check
import graphene
from dagster import PartitionsDefinition
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeDecisionType,
    AutoMaterializeRuleEvaluation,
    AutoMaterializeRuleEvaluationData,
    ParentUpdatedRuleEvaluationData,
    TextRuleEvaluationData,
    WaitingOnAssetsRuleEvaluationData,
)
from dagster._core.definitions.partition import SerializedPartitionsSubset
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.schema.errors import GrapheneError

from .asset_key import GrapheneAssetKey
from .auto_materialize_policy import GrapheneAutoMaterializeRule
from .util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GraphenePartitionKeys(graphene.ObjectType):
    partitionKeys = non_null_list(graphene.String)

    class Meta:
        name = "PartitionKeys"


class GraphenePartitionSubsetDeserializationError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "PartitionSubsetDeserializationError"


class GraphenePartitionKeysOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionKeys, GraphenePartitionSubsetDeserializationError)
        name = "PartitionKeysOrError"


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
    evaluation_data_tuple: Tuple[
        AutoMaterializeRuleEvaluationData,
        Optional[SerializedPartitionsSubset],
    ],
    partitions_def: Optional[PartitionsDefinition],
):
    rule_evaluation_data, serialized_partition_subset = evaluation_data_tuple

    if not serialized_partition_subset:
        partition_keys_or_error = None
    elif not partitions_def:
        partition_keys_or_error = GraphenePartitionSubsetDeserializationError(
            message="PartitionsDefinition not found, cannot display partition keys"
        )
    elif not serialized_partition_subset.can_deserialize(partitions_def):
        partition_keys_or_error = GraphenePartitionSubsetDeserializationError(
            message=(
                "Partition subset cannot be deserialized. The PartitionsDefinition may have"
                " changed."
            )
        )
    else:
        subset = serialized_partition_subset.deserialize(partitions_def)
        partition_keys_or_error = GraphenePartitionKeys(partitionKeys=subset.get_partition_keys())

    if isinstance(rule_evaluation_data, TextRuleEvaluationData):
        rule_evaluation_data = GrapheneTextRuleEvaluationData(text=rule_evaluation_data.text)
    elif isinstance(rule_evaluation_data, ParentUpdatedRuleEvaluationData):
        rule_evaluation_data = GrapheneParentMaterializedRuleEvaluationData(
            updatedAssetKeys=rule_evaluation_data.updated_asset_keys,
            willUpdateAssetKeys=rule_evaluation_data.will_update_asset_keys,
        )
    elif isinstance(rule_evaluation_data, WaitingOnAssetsRuleEvaluationData):
        rule_evaluation_data = GrapheneWaitingOnKeysRuleEvaluationData(
            waitingOnAssetKeys=rule_evaluation_data.waiting_on_asset_keys
        )
    elif rule_evaluation_data is not None:
        check.failed(f"Unexpected rule evaluation data type {type(rule_evaluation_data)}")

    return GrapheneAutoMaterializeRuleEvaluation(
        partitionKeysOrError=partition_keys_or_error, evaluationData=rule_evaluation_data
    )


def create_graphene_auto_materialize_rules_with_rule_evaluations(
    partition_subsets_by_condition: Sequence[
        Tuple[AutoMaterializeRuleEvaluation, Optional[SerializedPartitionsSubset]]
    ],
    partitions_def: Optional[PartitionsDefinition],
) -> Sequence[GrapheneAutoMaterializeRuleWithRuleEvaluations]:
    rule_mapping = defaultdict(list)
    for rule_evaluation, serialized_partition_subset in partition_subsets_by_condition:
        rule_mapping[rule_evaluation.rule_snapshot].append(
            (rule_evaluation.evaluation_data, serialized_partition_subset)
        )

    return [
        GrapheneAutoMaterializeRuleWithRuleEvaluations(
            rule=GrapheneAutoMaterializeRule(rule_snapshot),
            ruleEvaluations=[
                create_graphene_auto_materialize_rule_evaluation(tup, partitions_def)
                for tup in tups
            ],
        )
        for rule_snapshot, tups in rule_mapping.items()
    ]


class GrapheneAutoMaterializeAssetEvaluationRecord(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    evaluationId = graphene.NonNull(graphene.Int)
    numRequested = graphene.NonNull(graphene.Int)
    numSkipped = graphene.NonNull(graphene.Int)
    numDiscarded = graphene.NonNull(graphene.Int)
    rulesWithRuleEvaluations = non_null_list(GrapheneAutoMaterializeRuleWithRuleEvaluations)
    timestamp = graphene.NonNull(graphene.Float)
    runIds = non_null_list(graphene.String)
    rules = graphene.Field(graphene.List(graphene.NonNull(GrapheneAutoMaterializeRule)))

    class Meta:
        name = "AutoMaterializeAssetEvaluationRecord"

    def __init__(
        self,
        record: AutoMaterializeAssetEvaluationRecord,
        partitions_def: Optional[PartitionsDefinition],
    ):
        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            numRequested=record.evaluation.num_requested,
            numSkipped=record.evaluation.num_skipped,
            numDiscarded=record.evaluation.num_discarded,
            rulesWithRuleEvaluations=create_graphene_auto_materialize_rules_with_rule_evaluations(
                record.evaluation.partition_subsets_by_condition, partitions_def
            ),
            timestamp=record.timestamp,
            runIds=record.evaluation.run_ids,
            rules=(
                [
                    GrapheneAutoMaterializeRule(snapshot)
                    for snapshot in record.evaluation.rule_snapshots
                ]
                if record.evaluation.rule_snapshots is not None
                else None  # Return None if no rules serialized in evaluation
            ),
        )


class GrapheneAutoMaterializeAssetEvaluationRecords(graphene.ObjectType):
    records = non_null_list(GrapheneAutoMaterializeAssetEvaluationRecord)
    currentEvaluationId = graphene.Int()

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
