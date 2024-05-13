import datetime
import itertools
from typing import Any, Optional, Sequence

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
from dagster._model import DagsterModel


class SchedulingEvaluationResultNode(DagsterModel):
    """Represents the results of evaluating a single condition in the broader evaluation tree."""

    asset_key: AssetKey
    condition_unique_id: str

    true_slice: AssetSlice
    candidate_slice: AssetSlice
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

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
        node = SchedulingEvaluationResultNode(
            asset_key=asset_key,
            condition_unique_id=unique_id,
            true_slice=asset_graph_view.get_asset_slice_from_subset(
                condition_evaluation.true_subset
            ),
            candidate_slice=asset_graph_view.get_asset_slice_from_subset(candidate_subset),
            subsets_with_metadata=condition_evaluation.subsets_with_metadata,
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
            effective_dt=datetime.datetime.fromtimestamp(
                state.previous_tick_evaluation_timestamp or 0
            ),
            last_event_id=state.max_storage_id,
        )
        nodes = SchedulingEvaluationResultNode.nodes_for_evaluation(
            asset_graph_view, state, state.previous_evaluation
        )
        return SchedulingEvaluationInfo(temporal_context=temporal_context, evaluation_nodes=nodes)
