from dataclasses import dataclass
from typing import List, Optional, Sequence

from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes(storage_name="AndAssetCondition")
@dataclass(frozen=True, eq=False)
class AndAutomationCondition(AutomationCondition[T_EntityKey]):
    """This class represents the condition that all of its children evaluate to true."""

    operands: Sequence[AutomationCondition[T_EntityKey]]
    label: Optional[str] = None

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

    def evaluate(self, context: AutomationContext[T_EntityKey]) -> AutomationResult[T_EntityKey]:
        child_results: List[AutomationResult] = []
        true_slice = context.candidate_slice
        for i, child in enumerate(self.children):
            child_context = context.for_child_condition(
                child_condition=child, child_index=i, candidate_slice=true_slice
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_slice = true_slice.compute_intersection(child_result.true_slice)
        return AutomationResult(context, true_slice, child_results=child_results)


@whitelist_for_serdes(storage_name="OrAssetCondition")
@dataclass(frozen=True)
class OrAutomationCondition(AutomationCondition[T_EntityKey]):
    """This class represents the condition that any of its children evaluate to true."""

    operands: Sequence[AutomationCondition[T_EntityKey]]
    label: Optional[str] = None

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

    def evaluate(self, context: AutomationContext[T_EntityKey]) -> AutomationResult[T_EntityKey]:
        child_results: List[AutomationResult] = []
        true_slice = context.get_empty_slice()
        for i, child in enumerate(self.children):
            child_context = context.for_child_condition(
                child_condition=child, child_index=i, candidate_slice=context.candidate_slice
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_slice = true_slice.compute_union(child_result.true_slice)

        return AutomationResult(context, true_slice, child_results=child_results)


@whitelist_for_serdes(storage_name="NotAssetCondition")
@dataclass(frozen=True)
class NotAutomationCondition(AutomationCondition[T_EntityKey]):
    """This class represents the condition that none of its children evaluate to true."""

    operand: AutomationCondition[T_EntityKey]
    label: Optional[str] = None

    @property
    def description(self) -> str:
        return "Not"

    @property
    def name(self) -> str:
        return "NOT"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.operand]

    def evaluate(self, context: AutomationContext[T_EntityKey]) -> AutomationResult[T_EntityKey]:
        child_context = context.for_child_condition(
            child_condition=self.operand, child_index=0, candidate_slice=context.candidate_slice
        )
        child_result = self.operand.evaluate(child_context)
        true_slice = context.candidate_slice.compute_difference(child_result.true_slice)

        return AutomationResult(context, true_slice, child_results=[child_result])
