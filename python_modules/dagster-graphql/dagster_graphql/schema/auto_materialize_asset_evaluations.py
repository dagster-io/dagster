from typing import List, Optional, Tuple

import dagster._check as check
import graphene
from dagster import PartitionsDefinition
from dagster._core.definitions.auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    DownstreamFreshnessAutoMaterializeCondition,
    FreshnessAutoMaterializeCondition,
    MaxMaterializationsExceededAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from dagster._core.definitions.partition import SerializedPartitionsSubset
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.schema.errors import GrapheneError

from .util import non_null_list

GrapheneAutoMaterializeDecisionType = graphene.Enum.from_enum(AutoMaterializeDecisionType)


class GrapheneAutoMaterializeConditionInterface(graphene.Interface):
    decisionType = graphene.NonNull(GrapheneAutoMaterializeDecisionType)
    partitionKeys = graphene.List(graphene.NonNull(graphene.String))

    class Meta:
        name = "AutoMaterializeConditionWithDecisionType"


class GrapheneFreshnessAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "FreshnessAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionInterface,)


class GrapheneDownstreamFreshnessAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "DownstreamFreshnessAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionInterface,)


class GrapheneParentMaterializedAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "ParentMaterializedAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionInterface,)


class GrapheneMissingAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "MissingAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionInterface,)


class GrapheneParentOutdatedAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "ParentOutdatedAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionInterface,)


class GrapheneMaxMaterializationsExceededAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "MaxMaterializationsExceededAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionInterface,)


class GrapheneAutoMaterializeCondition(graphene.Union):
    class Meta:
        name = "AutoMaterializeCondition"
        types = (
            GrapheneFreshnessAutoMaterializeCondition,
            GrapheneDownstreamFreshnessAutoMaterializeCondition,
            GrapheneParentMaterializedAutoMaterializeCondition,
            GrapheneMissingAutoMaterializeCondition,
            GrapheneParentOutdatedAutoMaterializeCondition,
            GrapheneMaxMaterializationsExceededAutoMaterializeCondition,
        )


def create_graphene_auto_materialize_condition(
    condition_tuple: Tuple[AutoMaterializeCondition, Optional[SerializedPartitionsSubset]],
    partitions_def: Optional[PartitionsDefinition],
):
    condition, serialized_partition_subset = condition_tuple

    if serialized_partition_subset and serialized_partition_subset.can_deserialize(partitions_def):
        subset = serialized_partition_subset.deserialize(partitions_def)
        partition_keys = subset.get_partition_keys()
    else:
        partition_keys = None

    if isinstance(condition, FreshnessAutoMaterializeCondition):
        return GrapheneFreshnessAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeys=partition_keys
        )
    elif isinstance(condition, DownstreamFreshnessAutoMaterializeCondition):
        return GrapheneDownstreamFreshnessAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeys=partition_keys
        )
    elif isinstance(condition, ParentMaterializedAutoMaterializeCondition):
        return GrapheneParentMaterializedAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeys=partition_keys
        )
    elif isinstance(condition, MissingAutoMaterializeCondition):
        return GrapheneMissingAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeys=partition_keys
        )
    elif isinstance(condition, ParentOutdatedAutoMaterializeCondition):
        return GrapheneParentOutdatedAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeys=partition_keys
        )
    elif isinstance(condition, MaxMaterializationsExceededAutoMaterializeCondition):
        return GrapheneMaxMaterializationsExceededAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeys=partition_keys
        )
    else:
        check.failed(f"Unexpected condition type {type(condition)}")


class GrapheneAutoMaterializeAssetEvaluationRecord(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    evaluationId = graphene.NonNull(graphene.Int)
    numRequested = graphene.NonNull(graphene.Int)
    numSkipped = graphene.NonNull(graphene.Int)
    numDiscarded = graphene.NonNull(graphene.Int)
    conditions = non_null_list(GrapheneAutoMaterializeCondition)
    timestamp = graphene.NonNull(graphene.Float)

    class Meta:
        name = "AutoMaterializeAssetEvaluationRecord"

    def __init__(
        self,
        record: AutoMaterializeAssetEvaluationRecord,
        partitions_def=Optional[PartitionsDefinition],
    ):
        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            numRequested=record.evaluation.num_requested,
            numSkipped=record.evaluation.num_skipped,
            numDiscarded=record.evaluation.num_discarded,
            conditions=[
                create_graphene_auto_materialize_condition(c, partitions_def)
                for c in record.evaluation.partition_subsets_by_condition
            ],
            timestamp=record.timestamp,
        )


class GrapheneAutoMaterializeAssetEvaluationRecords(graphene.ObjectType):
    records = non_null_list(GrapheneAutoMaterializeAssetEvaluationRecord)

    class Meta:
        name = "AutoMaterializeAssetEvaluationRecords"

    def __init__(self, records: List[GrapheneAutoMaterializeAssetEvaluationRecord]):
        super().__init__(records=records)


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
