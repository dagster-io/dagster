from typing import Optional, Sequence

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._serdes.serdes import whitelist_for_serdes

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


@whitelist_for_serdes
class NewlyTrueCondition(AutomationCondition):
    operand: AutomationCondition

    @property
    def requires_cursor(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Condition newly became true."

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.operand]

    def _get_previous_child_true_slice(self, context: AutomationContext) -> Optional[AssetSlice]:
        """Returns the true slice of the child from the previous tick, which is stored in the
        extra state field of the cursor.
        """
        if not context.node_cursor:
            return None
        true_subset = context.node_cursor.get_extra_state(as_type=AssetSubset)
        if not true_subset:
            return None
        return context.asset_graph_view.get_asset_slice_from_subset(true_subset)

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        # evaluate child condition
        child_context = context.for_child_condition(
            self.operand,
            child_index=0,
            # must evaluate child condition over the entire slice to avoid missing state transitions
            candidate_slice=context.asset_graph_view.get_asset_slice(asset_key=context.asset_key),
        )
        child_result = self.operand.evaluate(child_context)

        # get the set of asset partitions of the child which newly became true
        newly_true_child_slice = child_result.true_slice.compute_difference(
            self._get_previous_child_true_slice(context)
            or context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)
        )

        return AutomationResult.create_from_children(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(newly_true_child_slice),
            child_results=[child_result],
            extra_state=child_result.true_subset,
        )
