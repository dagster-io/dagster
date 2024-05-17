from typing import Sequence

from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


@whitelist_for_serdes
class ScheduledSinceConditionCondition(SchedulingCondition):
    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return "Requested since condition last became true"

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return [self.operand]

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        # evaluate child condition
        child_context = context.for_child_condition(
            self.operand, child_index=0, candidate_slice=context.candidate_slice
        )
        child_result = self.operand.evaluate(child_context)

        empty_slice = context.asset_graph_view.create_empty_slice(context.asset_key)

        # get the set of asset partitions of the child which newly became true
        newly_true_child_slice = child_result.true_slice.compute_difference(
            child_context.previous_true_slice or empty_slice
        )

        # take the previous subset that this was true for
        true_slice = context.previous_true_slice or empty_slice
        # add in any asset partitions requested since the previous tick
        true_slice = true_slice.compute_union(context.previous_requested_slice or empty_slice)
        # remove any asset partitions that just became true
        true_slice = true_slice.compute_difference(newly_true_child_slice)

        return SchedulingResult.create_from_children(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(true_slice),
            child_results=[child_result],
        )
