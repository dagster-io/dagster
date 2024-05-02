from dagster._core.definitions.asset_key import AssetKey
from dagster._serdes.serdes import whitelist_for_serdes

from ..legacy.asset_condition import AssetCondition
from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext


class DepConditionWrapperCondition(SchedulingCondition):
    """Wrapper object which evaluates a condition against a dependency and returns a subset
    representing the subset of downstream asset which has at least one parent which evaluated to
    True.
    """

    dep_key: AssetKey
    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return f"{self.dep_key.to_user_string()}"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        # only evaluate parents of the current candidates
        dep_candidate_slice = context.candidate_slice.compute_parent_slice(self.dep_key)
        dep_context = context.for_child_condition(
            child_condition=self.operand, candidate_slice=dep_candidate_slice
        )

        # evaluate condition against the dependency
        dep_result = self.operand.evaluate(dep_context)

        # find all children of the true dep slice
        true_slice = dep_result.true_slice.compute_child_slice(context.asset_key)
        return SchedulingResult.create_from_children(
            context=context, true_slice=true_slice, child_results=[dep_result]
        )


@whitelist_for_serdes
class AnyDepsCondition(AssetCondition):
    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return "Any deps"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        dep_results = []
        true_slice = context.asset_graph_view.create_empty_slice(context.asset_key)

        dep_keys = context.asset_graph_view.asset_graph.get(context.asset_key).parent_keys
        for dep_key in dep_keys:
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition, candidate_slice=context.candidate_slice
                )
            )
            dep_results.append(dep_result)
            true_slice = true_slice.compute_union(dep_result.true_slice)

        true_slice = context.candidate_slice.compute_intersection(true_slice)
        return SchedulingResult.create_from_children(
            context, true_slice=true_slice, child_results=dep_results
        )


@whitelist_for_serdes
class AllDepsCondition(SchedulingCondition):
    operand: SchedulingCondition

    @property
    def description(self) -> str:
        return "All deps"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        dep_results = []
        true_slice = context.candidate_slice

        dep_keys = context.asset_graph_view.asset_graph.get(context.asset_key).parent_keys
        for dep_key in dep_keys:
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition, candidate_slice=context.candidate_slice
                )
            )
            dep_results.append(dep_result)
            true_slice = true_slice.compute_intersection(dep_result.true_slice)

        return SchedulingResult.create_from_children(
            context, true_slice=true_slice, child_results=dep_results
        )
