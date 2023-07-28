from typing import Optional, Tuple

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

from .asset_key import GrapheneAssetKey
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


class GrapheneAutoMaterializeConditionWithDecisionType(graphene.Interface):
    decisionType = graphene.NonNull(GrapheneAutoMaterializeDecisionType)
    partitionKeysOrError = graphene.Field(GraphenePartitionKeysOrError)

    class Meta:
        name = "AutoMaterializeConditionWithDecisionType"


class GrapheneFreshnessAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "FreshnessAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneDownstreamFreshnessAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "DownstreamFreshnessAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneParentMaterializedAutoMaterializeCondition(graphene.ObjectType):
    updatedAssetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))
    willUpdateAssetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))

    class Meta:
        name = "ParentMaterializedAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneMissingAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "MissingAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneParentOutdatedAutoMaterializeCondition(graphene.ObjectType):
    waitingOnAssetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))

    class Meta:
        name = "ParentOutdatedAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


class GrapheneMaxMaterializationsExceededAutoMaterializeCondition(graphene.ObjectType):
    class Meta:
        name = "MaxMaterializationsExceededAutoMaterializeCondition"
        interfaces = (GrapheneAutoMaterializeConditionWithDecisionType,)


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

    if isinstance(condition, FreshnessAutoMaterializeCondition):
        return GrapheneFreshnessAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeysOrError=partition_keys_or_error
        )
    elif isinstance(condition, DownstreamFreshnessAutoMaterializeCondition):
        return GrapheneDownstreamFreshnessAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeysOrError=partition_keys_or_error
        )
    elif isinstance(condition, ParentMaterializedAutoMaterializeCondition):
        return GrapheneParentMaterializedAutoMaterializeCondition(
            decisionType=condition.decision_type,
            partitionKeysOrError=partition_keys_or_error,
            updatedAssetKeys=condition.updated_asset_keys,
            willUpdateAssetKeys=condition.will_update_asset_keys,
        )
    elif isinstance(condition, MissingAutoMaterializeCondition):
        return GrapheneMissingAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeysOrError=partition_keys_or_error
        )
    elif isinstance(condition, ParentOutdatedAutoMaterializeCondition):
        return GrapheneParentOutdatedAutoMaterializeCondition(
            decisionType=condition.decision_type,
            partitionKeysOrError=partition_keys_or_error,
            waitingOnAssetKeys=condition.waiting_on_asset_keys,
        )
    elif isinstance(condition, MaxMaterializationsExceededAutoMaterializeCondition):
        return GrapheneMaxMaterializationsExceededAutoMaterializeCondition(
            decisionType=condition.decision_type, partitionKeysOrError=partition_keys_or_error
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
    runIds = non_null_list(graphene.String)

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
            conditions=[
                create_graphene_auto_materialize_condition(c, partitions_def)
                for c in record.evaluation.partition_subsets_by_condition
            ],
            timestamp=record.timestamp,
            runIds=record.evaluation.run_ids,
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
