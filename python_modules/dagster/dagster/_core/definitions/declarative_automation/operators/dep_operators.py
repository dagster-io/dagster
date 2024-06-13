from abc import abstractmethod
from typing import AbstractSet, Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._serdes.serdes import whitelist_for_serdes

from ..automation_condition import AutomationCondition, AutomationResult
from ..automation_context import AutomationContext


class DepConditionWrapperCondition(AutomationCondition):
    """Wrapper object which evaluates a condition against a dependency and returns a subset
    representing the subset of downstream asset which has at least one parent which evaluated to
    True.
    """

    dep_key: AssetKey
    operand: AutomationCondition

    @property
    def description(self) -> str:
        return f"{self.dep_key.to_user_string()}"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        # only evaluate parents of the current candidates
        dep_candidate_slice = context.candidate_slice.compute_parent_slice(self.dep_key)
        dep_context = context.for_child_condition(
            child_condition=self.operand, child_index=0, candidate_slice=dep_candidate_slice
        )

        # evaluate condition against the dependency
        dep_result = self.operand.evaluate(dep_context)

        # find all children of the true dep slice
        true_slice = dep_result.true_slice.compute_child_slice(context.asset_key)
        return AutomationResult.create_from_children(
            context=context, true_slice=true_slice, child_results=[dep_result]
        )


class DepCondition(AutomationCondition):
    operand: AutomationCondition
    allow_selection: Optional[AssetSelection] = None
    ignore_selection: Optional[AssetSelection] = None

    @property
    @abstractmethod
    def base_description(self) -> str: ...

    @property
    def description(self) -> str:
        description = f"{self.base_description} deps"
        if self.allow_selection is not None:
            description += f" within selection {self.allow_selection}"
        if self.ignore_selection is not None:
            description += f" except for {self.ignore_selection}"
        return description

    def allow(self, selection: AssetSelection) -> "DepCondition":
        """Returns a copy of this condition that will only consider dependencies within the provided
        AssetSelection.
        """
        allow_selection = (
            selection if self.allow_selection is None else selection | self.allow_selection
        )
        return self.model_copy(update={"allow_selection": allow_selection})

    def ignore(self, selection: AssetSelection) -> "DepCondition":
        """Returns a copy of this condition that will ignore dependencies within the provided
        AssetSelection.
        """
        ignore_selection = (
            selection if self.ignore_selection is None else selection | self.ignore_selection
        )
        return self.model_copy(update={"ignore_selection": ignore_selection})

    def _get_dep_keys(
        self, asset_key: AssetKey, asset_graph: BaseAssetGraph
    ) -> AbstractSet[AssetKey]:
        dep_keys = asset_graph.get(asset_key).parent_keys
        if self.allow_selection is not None:
            dep_keys &= self.allow_selection.resolve(asset_graph)
        if self.ignore_selection is not None:
            dep_keys -= self.ignore_selection.resolve(asset_graph)
        return dep_keys


@whitelist_for_serdes
class AnyDepsCondition(DepCondition):
    @property
    def base_description(self) -> str:
        return "Any"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        dep_results = []
        true_slice = context.asset_graph_view.create_empty_slice(asset_key=context.asset_key)

        for i, dep_key in enumerate(
            sorted(self._get_dep_keys(context.asset_key, context.asset_graph))
        ):
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition,
                    child_index=i,
                    candidate_slice=context.candidate_slice,
                )
            )
            dep_results.append(dep_result)
            true_slice = true_slice.compute_union(dep_result.true_slice)

        true_slice = context.candidate_slice.compute_intersection(true_slice)
        return AutomationResult.create_from_children(
            context, true_slice=true_slice, child_results=dep_results
        )


@whitelist_for_serdes
class AllDepsCondition(DepCondition):
    @property
    def base_description(self) -> str:
        return "All"

    def evaluate(self, context: AutomationContext) -> AutomationResult:
        dep_results = []
        true_slice = context.candidate_slice

        for i, dep_key in enumerate(
            sorted(self._get_dep_keys(context.asset_key, context.asset_graph))
        ):
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition,
                    child_index=i,
                    candidate_slice=context.candidate_slice,
                )
            )
            dep_results.append(dep_result)
            true_slice = true_slice.compute_intersection(dep_result.true_slice)

        return AutomationResult.create_from_children(
            context, true_slice=true_slice, child_results=dep_results
        )
