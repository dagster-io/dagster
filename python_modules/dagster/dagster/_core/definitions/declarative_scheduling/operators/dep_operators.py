from typing import TYPE_CHECKING, Dict, Iterable

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext

if TYPE_CHECKING:
    from dagster._core.asset_graph_view.asset_graph_view import AssetSlice


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
        # evaluate condition against the dependency
        dep_result = self.eval_child(context, self.operand, dep_candidate_slice)

        # find all children of the true dep slice
        true_slice = dep_result.true_slice.compute_child_slice(context.asset_key)
        return SchedulingResult.create_from_children(
            context=context, true_slice=true_slice, child_results=[dep_result]
        )


class DepCondition(SchedulingCondition):
    operand: SchedulingCondition

    def coll_from_keys(self, dep_keys: Iterable[AssetKey]) -> "DepConditionCollection":
        return DepConditionCollection(
            {
                dep_key: DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
                for dep_key in dep_keys
            }
        )


class DepConditionCollection:
    def __init__(self, conditions: Dict[AssetKey, DepConditionWrapperCondition]):
        self.conditions = list(conditions.items())
        self.keys = list(sorted(conditions.keys()))

    def eval(
        self, context: SchedulingContext, asset_key: AssetKey, asset_slice: "AssetSlice"
    ) -> SchedulingResult:
        for child_index, key_cond_tuple in enumerate(self.conditions):
            dep_key, child = key_cond_tuple
            if dep_key == asset_key:
                child_context = context.for_child_condition(
                    child_condition=child, child_index=child_index, candidate_slice=asset_slice
                )
                return child.evaluate(child_context)

        check.failed(f"Child {child} not found in parent condition")


@whitelist_for_serdes
class AnyDepsCondition(DepCondition):
    @property
    def description(self) -> str:
        return "Any deps"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        dep_results = []
        true_slice = context.asset_graph_view.create_empty_slice(context.asset_key)

        dep_keys = context.asset_graph_view.asset_graph.get(context.asset_key).parent_keys
        dep_coll = self.coll_from_keys(dep_keys)
        for dep_key in dep_coll.keys:
            dep_result = dep_coll.eval(context, dep_key, context.candidate_slice)
            true_slice = true_slice.compute_union(dep_result.true_slice)

        true_slice = context.candidate_slice.compute_intersection(true_slice)
        return SchedulingResult.create_from_children(
            context, true_slice=true_slice, child_results=dep_results
        )


@whitelist_for_serdes
class AllDepsCondition(DepCondition):
    @property
    def description(self) -> str:
        return "All deps"

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        dep_results = []
        true_slice = context.candidate_slice

        dep_keys = context.asset_graph_view.asset_graph.get(context.asset_key).parent_keys
        dep_coll = self.coll_from_keys(dep_keys)
        for dep_key in dep_coll.keys:
            dep_result = dep_coll.eval(context, dep_key, context.candidate_slice)
            dep_results.append(dep_result)
            true_slice = true_slice.compute_intersection(dep_result.true_slice)

        return SchedulingResult.create_from_children(
            context, true_slice=true_slice, child_results=dep_results
        )
