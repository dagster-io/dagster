from dagster._core.definitions.asset_key import AssetKey
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_condition import AssetCondition, AssetConditionResult
from .scheduling_context import SchedulingContext


class DepConditionWrapperCondition(AssetCondition):
    """Wrapper object which evaluates a condition against a dependency and returns a subset
    representing the subset of downstream asset which has at least one parent which evaluated to
    True.
    """

    dep_key: AssetKey
    operand: AssetCondition

    @property
    def description(self) -> str:
        return f"{self.dep_key.to_user_string()}"

    def evaluate(self, context: SchedulingContext) -> AssetConditionResult:
        # only evaluate parents of the current candidate subset
        dep_candidate_subset = context.candidate_slice.compute_parent_slice(
            self.dep_key
        ).convert_to_valid_asset_subset()
        dep_context = context.for_child_condition(
            asset_key=self.dep_key,
            child_condition=self.operand,
            candidate_subset=dep_candidate_subset,
        )

        # evaluate condition against the dependency
        dep_result = self.operand.evaluate(dep_context)

        # find all children of the true dep slice
        true_subset = dep_result.true_slice.compute_child_slice(
            context.asset_key
        ).convert_to_valid_asset_subset()
        return AssetConditionResult.create_from_children(
            context=context,
            true_subset=true_subset,
            child_results=[dep_result],
        )


@whitelist_for_serdes
class AnyDepsCondition(AssetCondition):
    operand: AssetCondition

    @property
    def description(self) -> str:
        return "Any deps"

    def evaluate(self, context: SchedulingContext) -> AssetConditionResult:
        dep_results = []
        true_subset = context.asset_graph_view.create_empty_slice(
            context.asset_key
        ).convert_to_valid_asset_subset()

        dep_keys = context.asset_graph_view.asset_graph.get(context.asset_key).parent_keys
        for dep_key in dep_keys:
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition, candidate_subset=context.candidate_subset
                )
            )
            dep_results.append(dep_result)
            true_subset |= dep_result.true_subset

        return AssetConditionResult.create_from_children(
            context, true_subset=context.candidate_subset & true_subset, child_results=dep_results
        )


@whitelist_for_serdes
class AllDepsCondition(AssetCondition):
    operand: AssetCondition

    @property
    def description(self) -> str:
        return "All deps"

    def evaluate(self, context: SchedulingContext) -> AssetConditionResult:
        dep_results = []
        true_subset = context.candidate_subset

        dep_keys = context.asset_graph_view.asset_graph.get(context.asset_key).parent_keys
        for dep_key in dep_keys:
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition, candidate_subset=context.candidate_subset
                )
            )
            dep_results.append(dep_result)
            true_subset &= dep_result.true_subset

        return AssetConditionResult.create_from_children(
            context, true_subset=true_subset, child_results=dep_results
        )
