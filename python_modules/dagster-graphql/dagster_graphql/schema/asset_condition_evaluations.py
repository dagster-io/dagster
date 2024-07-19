import enum
import itertools
from typing import Optional, Sequence, Union

import graphene
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
)
from dagster._core.definitions.partition import (
    DefaultPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
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

    def __init__(self, evaluation: AutomationConditionEvaluation):
        self._evaluation = evaluation
        if evaluation.true_subset.size > 0:
            status = AssetConditionEvaluationStatus.TRUE
        elif isinstance(evaluation.candidate_subset, AssetSubset) and (
            evaluation.candidate_subset.size > 0
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

    def __init__(self, evaluation: AutomationConditionEvaluation):
        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            description=evaluation.condition_snapshot.description,
            startTimestamp=evaluation.start_timestamp,
            endTimestamp=evaluation.end_timestamp,
            trueSubset=_coerce_subset(evaluation.true_subset),
            candidateSubset=_coerce_subset(evaluation.candidate_subset),
            numTrue=evaluation.true_subset.size,
            childUniqueIds=[
                child.condition_snapshot.unique_id for child in evaluation.child_evaluations
            ],
        )


class GrapheneSpecificPartitionAssetConditionEvaluationNode(graphene.ObjectType):
    uniqueId = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)

    metadataEntries = non_null_list(GrapheneMetadataEntry)
    status = graphene.NonNull(GrapheneAssetConditionEvaluationStatus)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "SpecificPartitionAssetConditionEvaluationNode"

    def __init__(self, evaluation: AutomationConditionEvaluation, partition_key: str):
        self._evaluation = evaluation
        self._partition_key = partition_key

        if not evaluation.true_subset.is_partitioned:
            # TODO: Remove on redesign (FOU-242)
            # This code allows the page to not error when displaying a specific partition's results
            # where a sub-condition is not partitioned. In these cases, we can treat the expression
            # as SKIPPED
            status = AssetConditionEvaluationStatus.SKIPPED
        elif partition_key in evaluation.true_subset.subset_value:
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
        root_evaluation: AutomationConditionEvaluation,
        partition_key: Optional[str] = None,
    ):
        all_evaluations = _flatten_evaluation(root_evaluation)
        if root_evaluation.true_subset.is_partitioned:
            if partition_key is None:
                evaluationNodes = [
                    GraphenePartitionedAssetConditionEvaluationNode(evaluation)
                    for evaluation in all_evaluations
                ]
            else:
                evaluationNodes = [
                    GrapheneSpecificPartitionAssetConditionEvaluationNode(evaluation, partition_key)
                    for evaluation in all_evaluations
                ]
        else:
            evaluationNodes = [
                GrapheneUnpartitionedAssetConditionEvaluationNode(evaluation)
                for evaluation in all_evaluations
            ]

        super().__init__(
            rootUniqueId=root_evaluation.condition_snapshot.unique_id,
            evaluationNodes=evaluationNodes,
        )


class GrapheneAutomationConditionEvaluationNode(graphene.ObjectType):
    uniqueId = graphene.NonNull(graphene.String)
    userLabel = graphene.Field(graphene.String)
    expandedLabel = non_null_list(graphene.String)

    startTimestamp = graphene.Field(graphene.Float)
    endTimestamp = graphene.Field(graphene.Float)

    numTrue = graphene.NonNull(graphene.Int)
    isPartitioned = graphene.NonNull(graphene.Boolean)

    trueSubset = graphene.NonNull(GrapheneAssetSubset)
    candidateSubset = graphene.Field(GrapheneAssetSubset)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "AutomationConditionEvaluationNode"

    def __init__(self, evaluation: AutomationConditionEvaluation):
        self._evaluation = evaluation
        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            expandedLabel=_get_expanded_label(evaluation),
            userLabel=evaluation.condition_snapshot.label,
            startTimestamp=evaluation.start_timestamp,
            endTimestamp=evaluation.end_timestamp,
            numTrue=evaluation.true_subset.size,
            isPartitioned=evaluation.true_subset.is_partitioned,
            trueSubset=_coerce_subset(evaluation.true_subset),
            candidateSubset=_coerce_subset(evaluation.candidate_subset),
            childUniqueIds=[
                child.condition_snapshot.unique_id for child in evaluation.child_evaluations
            ],
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

    isLegacy = graphene.NonNull(graphene.Boolean)

    # for legacy UI
    evaluation = graphene.NonNull(GrapheneAssetConditionEvaluation)

    rootUniqueId = graphene.NonNull(graphene.String)
    evaluationNodes = non_null_list(GrapheneAutomationConditionEvaluationNode)

    class Meta:
        name = "AssetConditionEvaluationRecord"

    def __init__(
        self,
        record: AutoMaterializeAssetEvaluationRecord,
        partitions_def: Optional[PartitionsDefinition],
    ):
        evaluation_with_run_ids = record.get_evaluation_with_run_ids(partitions_def)
        root_evaluation = evaluation_with_run_ids.evaluation

        flattened_evaluations = _flatten_evaluation(evaluation_with_run_ids.evaluation)

        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            timestamp=record.timestamp,
            runIds=evaluation_with_run_ids.run_ids,
            assetKey=GrapheneAssetKey(path=record.asset_key.path),
            numRequested=root_evaluation.true_subset.size,
            startTimestamp=root_evaluation.start_timestamp,
            endTimestamp=root_evaluation.end_timestamp,
            isLegacy=any(
                # RuleConditions are the legacy wrappers around AutoMaterializeRules
                node.condition_snapshot.class_name == "RuleCondition"
                for node in flattened_evaluations
            ),
            # for legacy UI
            evaluation=GrapheneAssetConditionEvaluation(root_evaluation),
            # for new UI
            rootUniqueId=root_evaluation.condition_snapshot.unique_id,
            evaluationNodes=[
                GrapheneAutomationConditionEvaluationNode(node) for node in flattened_evaluations
            ],
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


def _flatten_evaluation(
    e: AutomationConditionEvaluation,
) -> Sequence[AutomationConditionEvaluation]:
    # flattens the evaluation tree into a list of nodes
    return list(itertools.chain([e], *(_flatten_evaluation(ce) for ce in e.child_evaluations)))


def _coerce_subset(maybe_subset):
    if not isinstance(maybe_subset, AssetSubset):
        return None
    elif maybe_subset.is_partitioned:
        return GrapheneAssetSubset(maybe_subset)

    # TODO: Remove on redesign (FOU-242)
    # We create a fake partitioned asset subset out of an unpartitioned asset subset in
    # order to allow unpartitioned rows to not error when used in the partition-focused UI.
    if maybe_subset.size == 0:
        value = set()
    else:
        value = {"None"}

    return GrapheneAssetSubset(
        AssetSubset(asset_key=maybe_subset.asset_key, value=DefaultPartitionsSubset(value))
    )


def _get_expanded_label(
    evaluation: AutomationConditionEvaluation, use_label=False
) -> Sequence[str]:
    if use_label and evaluation.condition_snapshot.label is not None:
        return [evaluation.condition_snapshot.label]
    node_text = evaluation.condition_snapshot.name or evaluation.condition_snapshot.description
    child_labels = [
        f'({" ".join(_get_expanded_label(ce, use_label=True))})'
        for ce in evaluation.child_evaluations
    ]
    if len(child_labels) == 0:
        return [node_text]
    elif len(child_labels) == 1:
        return [node_text, f"{child_labels[0]}"]
    else:
        # intersperses node_text (e.g. AND) between each child label
        return list(itertools.chain(*itertools.zip_longest(child_labels, [], fillvalue=node_text)))[
            :-1
        ]
