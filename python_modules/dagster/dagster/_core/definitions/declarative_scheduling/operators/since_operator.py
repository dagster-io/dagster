from typing import Sequence, Tuple

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


@whitelist_for_serdes
class SinceCondition(SchedulingCondition):
    primary_condition: SchedulingCondition
    reference_condition: SchedulingCondition

    @property
    def description(self) -> str:
        return "Primary condition has become true since the last time the reference condition became true."

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return [self.primary_condition, self.reference_condition]

    def _compute_child_result_and_newly_true_slice(
        self,
        context: SchedulingContext,
        child_condition: SchedulingCondition,
        child_index: int,
    ) -> Tuple[SchedulingResult, AssetSlice]:
        # evaluate child condition
        child_context = context.for_child_condition(
            child_condition,
            child_index=child_index,
            # must evaluate child condition over the entire slice to avoid missing state transitions
            candidate_slice=context.asset_graph_view.get_asset_slice(context.asset_key),
        )
        child_result = child_condition.evaluate(child_context)

        # get the set of asset partitions of the child which newly became true
        newly_true_child_slice = child_result.true_slice.compute_difference(
            child_context.previous_true_slice
            or context.asset_graph_view.create_empty_slice(context.asset_key)
        )

        return child_result, newly_true_child_slice

    def compute_primary_result_and_newly_true_slice(
        self, context: SchedulingContext
    ) -> Tuple[SchedulingResult, AssetSlice]:
        return self._compute_child_result_and_newly_true_slice(
            context, self.primary_condition, child_index=0
        )

    def compute_reference_result_and_newly_true_slice(
        self, context: SchedulingContext
    ) -> Tuple[SchedulingResult, AssetSlice]:
        return self._compute_child_result_and_newly_true_slice(
            context, self.reference_condition, child_index=1
        )

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        primary_result, primary_newly_true = self.compute_primary_result_and_newly_true_slice(
            context
        )
        reference_result, reference_newly_true = self.compute_reference_result_and_newly_true_slice(
            context
        )

        # take the previous slice that this was true for
        true_slice = context.previous_true_slice or context.asset_graph_view.create_empty_slice(
            context.asset_key
        )
        # add in any newly true primary asset partitions
        true_slice = true_slice.compute_union(primary_newly_true)
        # remove any newly true reference asset partitions
        true_slice = true_slice.compute_difference(reference_newly_true)

        return SchedulingResult.create_from_children(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(true_slice),
            child_results=[primary_result, reference_result],
        )
