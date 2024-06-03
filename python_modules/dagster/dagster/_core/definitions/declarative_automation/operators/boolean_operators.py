from typing import List, Sequence

from dagster._annotations import experimental
from dagster._serdes.serdes import whitelist_for_serdes

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


@experimental
@whitelist_for_serdes
class AndAssetCondition(AutomationCondition):
    """This class represents the condition that all of its children evaluate to true."""

    operands: Sequence[AutomationCondition]

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return self.operands

    @property
    def description(self) -> str:
        return "All of"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        child_results: List[AutomationResult] = []
        true_slice = context.candidate_slice
        for i, child in enumerate(self.children):
            child_context = context.for_child_condition(
                child_condition=child, child_index=i, candidate_slice=true_slice
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_slice = true_slice.compute_intersection(child_result.true_slice)
        return AutomationResult.create_from_children(context, true_slice, child_results)


@experimental
@whitelist_for_serdes
class OrAssetCondition(AutomationCondition):
    """This class represents the condition that any of its children evaluate to true."""

    operands: Sequence[AutomationCondition]

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return self.operands

    @property
    def description(self) -> str:
        return "Any of"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        child_results: List[AutomationResult] = []
        true_slice = context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)
        for i, child in enumerate(self.children):
            child_context = context.for_child_condition(
                child_condition=child, child_index=i, candidate_slice=context.candidate_slice
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_slice = true_slice.compute_union(child_result.true_slice)

        return AutomationResult.create_from_children(context, true_slice, child_results)


@experimental
@whitelist_for_serdes
class NotAssetCondition(AutomationCondition):
    """This class represents the condition that none of its children evaluate to true."""

    operand: AutomationCondition

    @property
    def description(self) -> str:
        return "Not"

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.operand]

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        child_context = context.for_child_condition(
            child_condition=self.operand, child_index=0, candidate_slice=context.candidate_slice
        )
        child_result = self.operand.evaluate(child_context)
        true_slice = context.candidate_slice.compute_difference(child_result.true_slice)

        return AutomationResult.create_from_children(context, true_slice, [child_result])
