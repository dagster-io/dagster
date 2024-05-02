from typing import List, Sequence

from dagster._annotations import experimental
from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


@experimental
@whitelist_for_serdes
class AndAssetCondition(SchedulingCondition):
    """This class represents the condition that all of its children evaluate to true."""

    operands: Sequence[SchedulingCondition]

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return self.operands

    @property
    def description(self) -> str:
        return "All of"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        child_results: List[SchedulingResult] = []
        true_slice = context.candidate_slice
        for child in self.children:
            child_context = context.for_child_condition(
                child_condition=child, candidate_slice=true_slice
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_slice = true_slice.compute_intersection(child_result.true_slice)
        return SchedulingResult.create_from_children(context, true_slice, child_results)


@experimental
@whitelist_for_serdes
class OrAssetCondition(SchedulingCondition):
    """This class represents the condition that any of its children evaluate to true."""

    operands: Sequence[SchedulingCondition]

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return self.operands

    @property
    def description(self) -> str:
        return "Any of"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        child_results: List[SchedulingResult] = []
        true_slice = context.asset_graph_view.create_empty_slice(context.asset_key)
        for child in self.children:
            child_context = context.for_child_condition(
                child_condition=child, candidate_slice=context.candidate_slice
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_slice = true_slice.compute_union(child_result.true_slice)

        return SchedulingResult.create_from_children(context, true_slice, child_results)


@experimental
@whitelist_for_serdes
class NotAssetCondition(SchedulingCondition):
    """This class represents the condition that none of its children evaluate to true."""

    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return "Not"

    @property
    def children(self) -> Sequence[SchedulingCondition]:
        return [self.operand]

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        child_context = context.for_child_condition(
            child_condition=self.operand, candidate_slice=context.candidate_slice
        )
        child_result = self.operand.evaluate(child_context)
        true_slice = context.candidate_slice.compute_difference(child_result.true_slice)

        return SchedulingResult.create_from_children(context, true_slice, [child_result])
