import enum
import itertools
from collections.abc import Sequence
from typing import Optional, Union

import graphene
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
    AutomationConditionSnapshot,
)
from dagster._core.scheduler.instigation import AutoMaterializeAssetEvaluationRecord

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationNeedsMigrationError,
)
from dagster_graphql.schema.entity_key import GrapheneAssetKey, GrapheneEntityKey
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class AssetConditionEvaluationStatus(enum.Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    SKIPPED = "SKIPPED"


GrapheneAssetConditionEvaluationStatus = graphene.Enum.from_enum(AssetConditionEvaluationStatus)


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
        elif isinstance(evaluation.candidate_subset, SerializableEntitySubset) and (
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

    numTrue = graphene.NonNull(graphene.Int)
    numCandidates = graphene.Field(graphene.Int)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "PartitionedAssetConditionEvaluationNode"

    def __init__(self, evaluation: AutomationConditionEvaluation):
        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            description=evaluation.condition_snapshot.description,
            startTimestamp=evaluation.start_timestamp,
            endTimestamp=evaluation.end_timestamp,
            numTrue=evaluation.true_subset.size,
            numCandidates=evaluation.candidate_subset.size
            if isinstance(evaluation.candidate_subset, SerializableEntitySubset)
            else None,
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
            not isinstance(evaluation.candidate_subset, SerializableEntitySubset)
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
    numCandidates = graphene.Field(graphene.Int)

    isPartitioned = graphene.NonNull(graphene.Boolean)

    childUniqueIds = non_null_list(graphene.String)

    class Meta:
        name = "AutomationConditionEvaluationNode"

    def __init__(self, evaluation: AutomationConditionEvaluation):
        self._evaluation = evaluation
        super().__init__(
            uniqueId=evaluation.condition_snapshot.unique_id,
            expandedLabel=get_expanded_label(evaluation),
            userLabel=evaluation.condition_snapshot.label,
            startTimestamp=evaluation.start_timestamp,
            endTimestamp=evaluation.end_timestamp,
            numTrue=evaluation.true_subset.size,
            numCandidates=evaluation.candidate_subset.size
            if isinstance(evaluation.candidate_subset, SerializableEntitySubset)
            else None,
            isPartitioned=evaluation.true_subset.is_partitioned,
            childUniqueIds=[
                child.condition_snapshot.unique_id for child in evaluation.child_evaluations
            ],
        )


class GrapheneAssetConditionEvaluationRecord(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    evaluationId = graphene.NonNull(graphene.ID)
    runIds = non_null_list(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)

    assetKey = graphene.Field(GrapheneAssetKey)
    entityKey = graphene.NonNull(GrapheneEntityKey)
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
    ):
        evaluation_with_run_ids = record.get_evaluation_with_run_ids()
        root_evaluation = evaluation_with_run_ids.evaluation

        flattened_evaluations = _flatten_evaluation(evaluation_with_run_ids.evaluation)

        super().__init__(
            id=record.id,
            evaluationId=record.evaluation_id,
            timestamp=record.timestamp,
            runIds=evaluation_with_run_ids.run_ids,
            assetKey=GrapheneEntityKey.from_entity_key(record.key)
            if isinstance(record.key, AssetKey)
            else None,
            entityKey=GrapheneEntityKey.from_entity_key(record.key),
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


def get_expanded_label(
    item: Union[AutomationConditionEvaluation, AutomationConditionSnapshot],
    use_label=False,
) -> Sequence[str]:
    if isinstance(item, AutomationConditionSnapshot):
        label, name, description, children = (
            item.node_snapshot.label,
            item.node_snapshot.name,
            item.node_snapshot.description,
            item.children,
        )
    else:
        snapshot = item.condition_snapshot
        label, name, description, children = (
            snapshot.label,
            snapshot.name,
            snapshot.description,
            item.child_evaluations,
        )

    if use_label and label is not None:
        return [label]
    node_text = name or description
    child_labels = [f'({" ".join(get_expanded_label(c, use_label=True))})' for c in children]
    if len(child_labels) == 0:
        return [node_text]
    elif len(child_labels) == 1:
        return [node_text, f"{child_labels[0]}"]
    else:
        # intersperses node_text (e.g. AND) between each child label
        return list(itertools.chain(*itertools.zip_longest(child_labels, [], fillvalue=node_text)))[
            :-1
        ]
