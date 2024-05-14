import itertools
from typing import Any, NamedTuple, Optional, Sequence

from dagster._core.asset_graph_view.asset_graph_view import (
    AssetGraphView,
    AssetSlice,
    TemporalContext,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionEvaluation,
    AssetConditionEvaluationState,
    AssetSubsetWithMetadata,
)
from dagster._core.definitions.metadata import MetadataMapping
from dagster._model import DagsterModel
from dagster._utils import utc_datetime_from_timestamp


class AssetSliceWithMetadata(NamedTuple):
    asset_slice: AssetSlice
    metadata: MetadataMapping

    @staticmethod
    def from_asset_subset_with_metadata(
        *, asset_graph_view: AssetGraphView, asset_subset_with_metadata: AssetSubsetWithMetadata
    ) -> Optional["AssetSliceWithMetadata"]:
        metadata = asset_subset_with_metadata.metadata
        if metadata is None:
            return None
        asset_slice = asset_graph_view.get_asset_slice_from_subset(
            asset_subset_with_metadata.subset
        )
        if asset_slice is None:
            return None
        return AssetSliceWithMetadata(asset_slice=asset_slice, metadata=metadata)


class SchedulingEvaluationResultNode(DagsterModel):
    """Represents the results of evaluating a single condition in the broader evaluation tree."""

    asset_key: AssetKey
    condition_unique_id: str

    true_slice: Optional[AssetSlice]
    candidate_slice: Optional[AssetSlice]
    slices_with_metadata: Sequence[AssetSliceWithMetadata]

    extra_state: Any

    @staticmethod
    def nodes_for_evaluation(
        asset_graph_view: AssetGraphView,
        state: AssetConditionEvaluationState,
        condition_evaluation: AssetConditionEvaluation,
    ) -> Sequence["SchedulingEvaluationResultNode"]:
        unique_id = condition_evaluation.condition_snapshot.unique_id
        asset_key = condition_evaluation.asset_key
        # we store AllPartitionsSubset as a sentinel value to avoid serializing the entire set of
        # partitions on each tick. this logic handles converting that back to an AllPartitionsSubset
        # at read time.
        candidate_subset = (
            condition_evaluation.candidate_subset
            if isinstance(condition_evaluation.candidate_subset, AssetSubset)
            else asset_graph_view.get_asset_slice(asset_key).convert_to_valid_asset_subset()
        )

        # only carry forward subsets that are compatible with the current partitions def
        slices_with_metadata = list(
            filter(
                None,
                [
                    AssetSliceWithMetadata.from_asset_subset_with_metadata(
                        asset_graph_view=asset_graph_view,
                        asset_subset_with_metadata=subset_with_metadata,
                    )
                    for subset_with_metadata in condition_evaluation.subsets_with_metadata
                ],
            )
        )
        node = SchedulingEvaluationResultNode(
            asset_key=asset_key,
            condition_unique_id=unique_id,
            true_slice=asset_graph_view.get_asset_slice_from_subset(
                condition_evaluation.true_subset
            ),
            candidate_slice=asset_graph_view.get_asset_slice_from_subset(candidate_subset),
            slices_with_metadata=slices_with_metadata,
            extra_state=state.extra_state_by_unique_id.get(unique_id),
        )
        child_nodes = [
            SchedulingEvaluationResultNode.nodes_for_evaluation(asset_graph_view, state, child)
            for child in condition_evaluation.child_evaluations
        ]
        return list(itertools.chain([node], *child_nodes))


class SchedulingEvaluationInfo(DagsterModel):
    """Represents computed information for the entire evaluation tree."""

    temporal_context: TemporalContext
    evaluation_nodes: Sequence[SchedulingEvaluationResultNode]
    requested_slice: Optional[AssetSlice]

    def get_evaluation_node(self, unique_id: str) -> Optional[SchedulingEvaluationResultNode]:
        for node in self.evaluation_nodes:
            if node.condition_unique_id == unique_id:
                return node
        return None

    @staticmethod
    def from_asset_condition_evaluation_state(
        asset_graph_view: AssetGraphView, state: AssetConditionEvaluationState
    ) -> "SchedulingEvaluationInfo":
        temporal_context = TemporalContext(
            effective_dt=utc_datetime_from_timestamp(state.previous_tick_evaluation_timestamp or 0),
            last_event_id=state.max_storage_id,
        )
        nodes = SchedulingEvaluationResultNode.nodes_for_evaluation(
            asset_graph_view, state, state.previous_evaluation
        )
        requested_slice = asset_graph_view.get_asset_slice_from_subset(state.true_subset)
        return SchedulingEvaluationInfo(
            temporal_context=temporal_context,
            evaluation_nodes=nodes,
            requested_slice=requested_slice,
        )
