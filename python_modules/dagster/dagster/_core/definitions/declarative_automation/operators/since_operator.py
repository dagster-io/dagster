from typing import Optional, Sequence

from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
class SinceCondition(BuiltinAutomationCondition[T_EntityKey]):
    trigger_condition: AutomationCondition[T_EntityKey]
    reset_condition: AutomationCondition[T_EntityKey]
    label: Optional[str] = None

    @property
    def description(self) -> str:
        return (
            "Trigger condition has become true since the last time the reset condition became true."
        )

    @property
    def name(self) -> str:
        return "SINCE"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.trigger_condition, self.reset_condition]

    def evaluate(self, context: AutomationContext[T_EntityKey]) -> AutomationResult[T_EntityKey]:
        # must evaluate child condition over the entire slice to avoid missing state transitions
        child_candidate_slice = context.asset_graph_view.get_full_slice(key=context.key)

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
        true_slice = context.previous_true_slice or context.get_empty_slice()

        # add in any newly true trigger asset partitions
        true_slice = true_slice.compute_union(trigger_result.true_slice)
        # remove any newly true reset asset partitions
        true_slice = true_slice.compute_difference(reset_result.true_slice)

        return AutomationResult(
            context=context, true_slice=true_slice, child_results=[trigger_result, reset_result]
        )
