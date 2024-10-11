from typing import List, Sequence

import dagster._check as check
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes(storage_name="AndAssetCondition")
@record
class AndAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """This class represents the condition that all of its children evaluate to true."""

    operands: Sequence[AutomationCondition[T_EntityKey]]

    @property
    def description(self) -> str:
        return "All of"

    @property
    def name(self) -> str:
        return "AND"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return self.operands

    @property
    def requires_cursor(self) -> bool:
        return False

    async def evaluate(
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        child_results: List[AutomationResult] = []
        true_subset = context.candidate_subset
        for i, child in enumerate(self.children):
            child_context = context.for_child_condition(
                child_condition=child, child_index=i, candidate_subset=true_subset
            )
            child_result = await child_context.evaluate_async()
            child_results.append(child_result)
            true_subset = true_subset.compute_intersection(child_result.true_subset)
        return AutomationResult(context, true_subset, child_results=child_results)

    def without(self, condition: AutomationCondition) -> "AndAutomationCondition":
        """Returns a copy of this condition without the specified child condition."""
        check.param_invariant(
            condition in self.operands, "condition", "Condition not found in operands"
        )
        operands = [child for child in self.operands if child != condition]
        if len(operands) < 2:
            check.failed("Cannot have fewer than 2 operands in an AndAutomationCondition")
        return AndAutomationCondition(
            operands=[child for child in self.operands if child != condition]
        )


@whitelist_for_serdes(storage_name="OrAssetCondition")
@record
class OrAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """This class represents the condition that any of its children evaluate to true."""

    operands: Sequence[AutomationCondition[T_EntityKey]]

    @property
    def description(self) -> str:
        return "Any of"

    @property
    def name(self) -> str:
        return "OR"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return self.operands

    @property
    def requires_cursor(self) -> bool:
        return False

    async def evaluate(
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        child_results: List[AutomationResult] = []
        true_subset = context.get_empty_subset()
        for i, child in enumerate(self.children):
            child_context = context.for_child_condition(
                child_condition=child, child_index=i, candidate_subset=context.candidate_subset
            )
            child_result = await child_context.evaluate_async()
            child_results.append(child_result)
            true_subset = true_subset.compute_union(child_result.true_subset)

        return AutomationResult(context, true_subset, child_results=child_results)


@whitelist_for_serdes(storage_name="NotAssetCondition")
@record
class NotAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """This class represents the condition that none of its children evaluate to true."""

    operand: AutomationCondition[T_EntityKey]

    @property
    def description(self) -> str:
        return "Not"

    @property
    def name(self) -> str:
        return "NOT"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.operand]

    async def evaluate(
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        child_context = context.for_child_condition(
            child_condition=self.operand, child_index=0, candidate_subset=context.candidate_subset
        )
        child_result = await child_context.evaluate_async()
        true_subset = context.candidate_subset.compute_difference(child_result.true_subset)

        return AutomationResult(context, true_subset, child_results=[child_result])
