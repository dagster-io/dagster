from typing import Sequence

from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


@whitelist_for_serdes
class NewlyTrueCondition(SchedulingCondition):
    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return "Condition newly became true."

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return [self.operand]

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        # evaluate child condition
        child_context = context.for_child_condition(
            self.operand,
            child_index=0,
            # must evaluate child condition over the entire slice to avoid missing state transitions
            candidate_slice=context.asset_graph_view.get_asset_slice(context.asset_key),
        )
        child_result = self.operand.evaluate(child_context)

        # get the set of asset partitions of the child which newly became true
        newly_true_child_slice = child_result.true_slice.compute_difference(
            child_context.previous_true_slice
            or context.asset_graph_view.create_empty_slice(context.asset_key)
        )

        return SchedulingResult.create_from_children(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(newly_true_child_slice),
            child_results=[child_result],
        )
