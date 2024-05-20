from typing import Sequence, Tuple

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    AssetSliceWithMetadata,
)
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext

_TARGET_EVER_TRUE_METADATA_KEY = "target_was_true"


@whitelist_for_serdes
class TriggerSinceTargetCondition(SchedulingCondition):
    trigger_condition: SchedulingCondition
    target_condition: SchedulingCondition

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return [self.trigger_condition, self.target_condition]

    @property
    def description(self) -> str:
        return "Trigger condition has become true since target condition last became true"

    def _get_target_ever_true_slice_with_metadata(
        self, context: SchedulingContext, y_result: SchedulingResult
    ) -> AssetSliceWithMetadata:
        """Keep track of the slice that has ever been true for the designated target condition."""
        previous_subsets_with_metadata = (
            context.previous_evaluation_node.slices_with_metadata
            if context.previous_evaluation_node
            else []
        )

        previous_slice = context.asset_graph_view.create_empty_slice(context.asset_key)
        if len(previous_subsets_with_metadata) == 1:
            previous_value = next(iter(previous_subsets_with_metadata))
            if _TARGET_EVER_TRUE_METADATA_KEY in previous_value.metadata:
                previous_slice = previous_value.asset_slice

        return AssetSliceWithMetadata(
            asset_slice=previous_slice.compute_union(y_result.true_slice),
            metadata={_TARGET_EVER_TRUE_METADATA_KEY: MetadataValue.bool(True)},
        )

    def _compute_child_result_and_newly_true_slice(
        self,
        context: SchedulingContext,
        child_condition: SchedulingCondition,
        child_index: int,
    ) -> Tuple[SchedulingResult, AssetSlice]:
        # evaluate child condition
        child_context = context.for_child_condition(
            child_condition, child_index=child_index, candidate_slice=context.candidate_slice
        )
        child_result = child_condition.evaluate(child_context)

        # get the set of asset partitions of the child which newly became true
        newly_true_child_slice = child_result.true_slice.compute_difference(
            child_context.previous_true_slice
            or context.asset_graph_view.create_empty_slice(context.asset_key)
        )

        return child_result, newly_true_child_slice

    def compute_trigger_result_and_newly_true_slice(
        self, context: SchedulingContext
    ) -> Tuple[SchedulingResult, AssetSlice]:
        return self._compute_child_result_and_newly_true_slice(
            context, self.trigger_condition, child_index=0
        )

    def compute_target_result_and_newly_true_slice(
        self, context: SchedulingContext
    ) -> Tuple[SchedulingResult, AssetSlice]:
        return self._compute_child_result_and_newly_true_slice(
            context, self.target_condition, child_index=1
        )

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        trigger_result, trigger_newly_true = self.compute_trigger_result_and_newly_true_slice(
            context
        )
        target_result, target_newly_true = self.compute_target_result_and_newly_true_slice(context)

        # get the slice that target has ever been true for
        target_ever_true_slice_with_metadata = self._get_target_ever_true_slice_with_metadata(
            context, target_result
        )

        # take the previous slice that this was true for
        true_slice = context.previous_true_slice or context.asset_graph_view.create_empty_slice(
            context.asset_key
        )
        # add in any newly true trigger asset partitions for which the target has ever been true
        true_slice = true_slice.compute_union(
            trigger_newly_true.compute_intersection(
                target_ever_true_slice_with_metadata.asset_slice
            )
        )
        # remove any newly true target asset partitions
        true_slice = true_slice.compute_difference(target_newly_true)

        return SchedulingResult.create_from_children(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(true_slice),
            child_results=[trigger_result, target_result],
            slices_with_metadata=[target_ever_true_slice_with_metadata],
        )
