import enum
import itertools
from typing import Optional, Sequence, Union

import graphene
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AssetConditionEvaluation,
)
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
)
from dagster_graphql.schema.metadata import GrapheneMetadataEntry

from .asset_key import GrapheneAssetKey
from .partition_sets import GraphenePartitionKeyRange
from .util import ResolveInfo, non_null_list


class AssetConditionEvaluationStatus(enum.Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    SKIPPED = "SKIPPED"


GrapheneAssetConditionEvaluationStatus = graphene.Enum.from_enum(AssetConditionEvaluationStatus)


class GrapheneAssetSubsetValue(graphene.ObjectType):
    class Meta:
        name = "AssetSubsetValue"

    boolValue = graphene.Field(graphene.Boolean)
    partitionKeys = graphene.List(graphene.NonNull(graphene.String))
    partitionKeyRanges = graphene.List(graphene.NonNull(GraphenePartitionKeyRange))

    isPartitioned = graphene.NonNull(graphene.Boolean)

    def __init__(self, value: Union[bool, PartitionsSubset]):
        bool_value, partition_keys, partition_key_ranges = None, None, None
        if isinstance(value, bool):
            bool_value = value
        elif isinstance(value, BaseTimeWindowPartitionsSubset):
            partition_key_ranges = [
                GraphenePartitionKeyRange(start, end)
                for start, end in value.get_partition_key_ranges(value.partitions_def)
            ]
            partition_keys = value.get_partition_keys()
        else:
            partition_keys = value.get_partition_keys()

        super().__init__(
            boolValue=bool_value,
            partitionKeys=partition_keys,
            partitionKeyRanges=partition_key_ranges,
        )

    def resolve_isPartitioned(self, graphene_info: ResolveInfo) -> bool:
        return self.boolValue is not None


class GrapheneAssetSubset(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    subsetValue = graphene.NonNull(GrapheneAssetSubsetValue)

    class Meta:
        name = "AssetSubset"

    def __init__(self, asset_subset: AssetSubset):
        super().__init__(
            assetKey=GrapheneAssetKey(path=asset_subset.asset_key.path),
            subsetValue=GrapheneAssetSubsetValue(asset_subset.subset_value),
        )


class GrapheneUnpartitionedAssetConditionEvaluationNode(graphene.ObjectType):
    uniqueId = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)

    startTimestamp = graphene.Field(graphene.Float)
    endTimestamp = graphene.Field(graphene.Float)

    metadataEntries = non_null_list(GrapheneMetadataEntry)
    status = graphene.NonNull(GrapheneAssetConditionEvaluationStatus)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "UnpartitionedAssetConditionEvaluationNode"

    def __init__(self, evaluation: AssetConditionEvaluation):
        self._evaluation = evaluation
        if evaluation.true_subset.bool_value:
            status = AssetConditionEvaluationStatus.TRUE
        elif (
            isinstance(evaluation.candidate_subset, AssetSubset)
            and evaluation.candidate_subset.bool_value
        ):
            status = AssetConditionEvaluationStatus.FALSE
        else:
            status = AssetConditionEvaluationStatus.SKIPPED

        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            description=evaluation.condition_snapshot.description,
            startTimestamp=evaluation.start_timestamp,
            endTimestamp=evaluation.end_timestamp,
            status=status,
            childUniqueIds=[
                child.condition_snapshot.unique_id for child in evaluation.child_evaluations
            ],
        )

    def resolve_metadataEntries(
        self, graphene_info: ResolveInfo
    ) -> Sequence[GrapheneMetadataEntry]:
        metadata = next(
            (subset.metadata for subset in self._evaluation.subsets_with_metadata),
            {},
        )
        return list(iterate_metadata_entries(metadata))


class GraphenePartitionedAssetConditionEvaluationNode(graphene.ObjectType):
    uniqueId = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)

    startTimestamp = graphene.Field(graphene.Float)
    endTimestamp = graphene.Field(graphene.Float)

    trueSubset = graphene.NonNull(GrapheneAssetSubset)
    candidateSubset = graphene.Field(GrapheneAssetSubset)

    numTrue = graphene.NonNull(graphene.Int)
    numFalse = graphene.Field(graphene.Int)
    numSkipped = graphene.Field(graphene.Int)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "PartitionedAssetConditionEvaluationNode"

    def __init__(
        self,
        evaluation: AssetConditionEvaluation,
        partitions_def: Optional[PartitionsDefinition],
    ):
        self._partitions_def = partitions_def
        self._true_subset = evaluation.true_subset

        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            description=evaluation.condition_snapshot.description,
            startTimestamp=evaluation.start_timestamp,
            endTimestamp=evaluation.end_timestamp,
            trueSubset=GrapheneAssetSubset(evaluation.true_subset),
            candidateSubset=GrapheneAssetSubset(evaluation.candidate_subset)
            if isinstance(evaluation.candidate_subset, AssetSubset)
            else None,
            childUniqueIds=[
                child.condition_snapshot.unique_id for child in evaluation.child_evaluations
            ],
        )

    def resolve_numTrue(self, graphene_info: ResolveInfo) -> int:
        return self._true_subset.size


class GrapheneSpecificPartitionAssetConditionEvaluationNode(graphene.ObjectType):
    uniqueId = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)

    metadataEntries = non_null_list(GrapheneMetadataEntry)
    status = graphene.NonNull(GrapheneAssetConditionEvaluationStatus)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "SpecificPartitionAssetConditionEvaluationNode"

    def __init__(self, evaluation: AssetConditionEvaluation, partition_key: str):
        self._evaluation = evaluation
        self._partition_key = partition_key

        if partition_key in evaluation.true_subset.subset_value:
            status = AssetConditionEvaluationStatus.TRUE
        elif (
            not isinstance(evaluation.candidate_subset, AssetSubset)
            or partition_key in evaluation.candidate_subset.subset_value
        ):
            status = AssetConditionEvaluationStatus.FALSE
        else:
            status = AssetConditionEvaluationStatus.SKIPPED

        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            description=evaluation.condition_snapshot.description,
            status=status,
            childUniqueIds=[
                child.condition_snapshot.unique_id for child in evaluation.child_evaluations
            ],
        )

    def resolve_metadataEntries(
        self, graphene_info: ResolveInfo
    ) -> Sequence[GrapheneMetadataEntry]:
        # find the metadata associated with a subset that contains this partition key
        metadata = next(
            (
                subset.metadata
                for subset in self._evaluation.subsets_with_metadata
                if self._partition_key in subset.subset.subset_value
            ),
            {},
        )
        return list(iterate_metadata_entries(metadata))


class GrapheneAssetConditionEvaluationNode(graphene.Union):
    class Meta:
        types = (
            GrapheneUnpartitionedAssetConditionEvaluationNode,
            GraphenePartitionedAssetConditionEvaluationNode,
            GrapheneSpecificPartitionAssetConditionEvaluationNode,
        )
        name = "AssetConditionEvaluationNode"


class GrapheneAssetConditionEvaluation(graphene.ObjectType):
    rootUniqueId = graphene.NonNull(graphene.String)
    evaluationNodes = non_null_list(GrapheneAssetConditionEvaluationNode)

    class Meta:
        name = "AssetConditionEvaluation"

    def __init__(
        self,
        evaluation: AssetConditionEvaluation,
        partitions_def: Optional[PartitionsDefinition],
        partition_key: Optional[str] = None,
    ):
        # flatten the evaluation tree into a list of nodes
        def _flatten(e: AssetConditionEvaluation) -> Sequence[AssetConditionEvaluation]:
            return list(itertools.chain([e], *(_flatten(ce) for ce in e.child_evaluations)))

        all_nodes = _flatten(evaluation)

        if evaluation.true_subset.is_partitioned:
            if partition_key is None:
                evaluationNodes = [
                    GraphenePartitionedAssetConditionEvaluationNode(evaluation, partitions_def)
                    for evaluation in all_nodes
                ]
            else:
                evaluationNodes = [
                    GrapheneSpecificPartitionAssetConditionEvaluationNode(evaluation, partition_key)
                    for evaluation in all_nodes
                ]
        else:
            evaluationNodes = [
                GrapheneUnpartitionedAssetConditionEvaluationNode(evaluation)
                for evaluation in all_nodes
            ]

        super().__init__(
            rootUniqueId=evaluation.condition_snapshot.unique_id,
            evaluationNodes=evaluationNodes,
        )


class GrapheneAssetConditionEvaluationRecord(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    evaluationId = graphene.NonNull(graphene.Int)
    runIds = non_null_list(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)

    assetKey = graphene.NonNull(GrapheneAssetKey)
    numRequested = graphene.NonNull(graphene.Int)

    startTimestamp = graphene.Field(graphene.Float)
    endTimestamp = graphene.Field(graphene.Float)

    evaluation = graphene.NonNull(GrapheneAssetConditionEvaluation)

    class Meta:
        name = "AssetConditionEvaluationRecord"

    def __init__(
        self,
        record: AutoMaterializeAssetEvaluationRecord,
        partitions_def: Optional[PartitionsDefinition],
    ):
        evaluation_with_run_ids = record.get_evaluation_with_run_ids(partitions_def)

        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            timestamp=record.timestamp,
            runIds=evaluation_with_run_ids.run_ids,
            assetKey=GrapheneAssetKey(path=record.asset_key.path),
            numRequested=evaluation_with_run_ids.evaluation.true_subset.size,
            startTimestamp=evaluation_with_run_ids.evaluation.start_timestamp,
            endTimestamp=evaluation_with_run_ids.evaluation.end_timestamp,
            evaluation=GrapheneAssetConditionEvaluation(
                evaluation_with_run_ids.evaluation, partitions_def
            ),
        )


class GrapheneAssetConditionEvaluationRecords(graphene.ObjectType):
    records = non_null_list(GrapheneAssetConditionEvaluationRecord)

    class Meta:
        name = "AssetConditionEvaluationRecords"


class GrapheneAssetConditionEvaluationRecordsOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetConditionEvaluationRecords,
            GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
        )
        name = "AssetConditionEvaluationRecordsOrError"
