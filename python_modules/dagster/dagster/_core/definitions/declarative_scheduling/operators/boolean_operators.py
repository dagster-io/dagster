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
        true_subset = context.candidate_subset
        for child in self.children:
            child_context = context.for_child_condition(
                child_condition=child, candidate_subset=true_subset
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_subset &= child_result.true_subset
        return SchedulingResult.create_from_children(context, true_subset, child_results)


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
        true_subset = context.asset_graph_view.create_empty_slice(
            context.asset_key
        ).convert_to_valid_asset_subset()
        for child in self.children:
            child_context = context.for_child_condition(
                child_condition=child, candidate_subset=context.candidate_subset
            )
            child_result = child.evaluate(child_context)
            child_results.append(child_result)
            true_subset |= child_result.true_subset
        return SchedulingResult.create_from_children(context, true_subset, child_results)


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
            child_condition=self.operand, candidate_subset=context.candidate_subset
        )
        child_result = self.operand.evaluate(child_context)
        true_subset = context.candidate_subset - child_result.true_subset

        return SchedulingResult.create_from_children(context, true_subset, [child_result])
