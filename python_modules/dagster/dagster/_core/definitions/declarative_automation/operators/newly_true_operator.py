from typing import Optional, Sequence

from dagster._core.asset_graph_view.asset_graph_view import EntitySlice
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.entity_subset import EntitySubset
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
class NewlyTrueCondition(BuiltinAutomationCondition[T_EntityKey]):
    operand: AutomationCondition[T_EntityKey]

    @property
    def description(self) -> str:
        return "Condition newly became true."

    @property
    def name(self) -> str:
        return "NEWLY_TRUE"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.operand]

    def _get_previous_child_true_slice(
        self, context: AutomationContext[T_EntityKey]
    ) -> Optional[EntitySlice[T_EntityKey]]:
        """Returns the true slice of the child from the previous tick, which is stored in the
        extra state field of the cursor.
        """
        true_subset = context.get_structured_cursor(as_type=EntitySubset)
        if not true_subset:
            return None
        return context.asset_graph_view.get_slice_from_subset(true_subset)

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        # evaluate child condition
        child_context = context.for_child_condition(
            self.operand,
            child_index=0,
            # must evaluate child condition over the entire slice to avoid missing state transitions
            candidate_slice=context.asset_graph_view.get_full_slice(key=context.key),
        )
        child_result = self.operand.evaluate(child_context)

        # get the set of asset partitions of the child which newly became true
        newly_true_child_slice = child_result.true_slice.compute_difference(
            self._get_previous_child_true_slice(context) or context.get_empty_slice()
        )

        return AutomationResult(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(newly_true_child_slice),
            child_results=[child_result],
            structured_cursor=child_result.true_slice.convert_to_serializable_subset(),
        )
