import asyncio
from collections.abc import Sequence

from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class SinceCondition(BuiltinAutomationCondition[T_EntityKey]):
    trigger_condition: AutomationCondition[T_EntityKey]
    reset_condition: AutomationCondition[T_EntityKey]

    @property
    def name(self) -> str:
        return "SINCE"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.trigger_condition, self.reset_condition]

    async def evaluate(
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        # must evaluate child condition over the entire subset to avoid missing state transitions
        child_candidate_subset = context.asset_graph_view.get_full_subset(key=context.key)

        # compute result for trigger and reset conditions
        trigger_result, reset_result = await asyncio.gather(
            *[
                context.for_child_condition(
                    self.trigger_condition, child_index=0, candidate_subset=child_candidate_subset
                ).evaluate_async(),
                context.for_child_condition(
                    self.reset_condition, child_index=1, candidate_subset=child_candidate_subset
                ).evaluate_async(),
            ]
        )

        # take the previous subset that this was true for
        true_subset = context.previous_true_subset or context.get_empty_subset()

        # add in any newly true trigger asset partitions
        true_subset = true_subset.compute_union(trigger_result.true_subset)
        # remove any newly true reset asset partitions
        true_subset = true_subset.compute_difference(reset_result.true_subset)

        return AutomationResult(
            context=context, true_subset=true_subset, child_results=[trigger_result, reset_result]
        )
