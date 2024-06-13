from typing import Sequence

from dagster._serdes.serdes import whitelist_for_serdes

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


@whitelist_for_serdes
class SinceCondition(AutomationCondition):
    trigger_condition: AutomationCondition
    reset_condition: AutomationCondition

    @property
    def requires_cursor(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return (
            "Trigger condition has become true since the last time the reset condition became true."
        )

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.trigger_condition, self.reset_condition]

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        # must evaluate child condition over the entire slice to avoid missing state transitions
        child_candidate_slice = context.asset_graph_view.get_asset_slice(
            asset_key=context.asset_key
        )

        # compute result for trigger condition
        trigger_context = context.for_child_condition(
            self.trigger_condition, child_index=0, candidate_slice=child_candidate_slice
        )
        trigger_result = self.trigger_condition.evaluate(trigger_context)

        # compute result for reset condition
        reset_context = context.for_child_condition(
            self.reset_condition, child_index=1, candidate_slice=child_candidate_slice
        )
        reset_result = self.reset_condition.evaluate(reset_context)

        # take the previous slice that this was true for
        true_slice = context.previous_true_slice or context.asset_graph_view.create_empty_slice(
            asset_key=context.asset_key
        )
        # add in any newly true trigger asset partitions
        true_slice = true_slice.compute_union(trigger_result.true_slice)
        # remove any newly true reset asset partitions
        true_slice = true_slice.compute_difference(reset_result.true_slice)

        return AutomationResult.create_from_children(
            context=context, true_slice=true_slice, child_results=[trigger_result, reset_result]
        )
