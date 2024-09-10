from abc import abstractmethod
from typing import AbstractSet

from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._serdes.serdes import whitelist_for_serdes


class CheckCondition(BuiltinAutomationCondition[AssetKey]):
    operand: AutomationCondition[AssetCheckKey]
    blocking: bool

    @property
    @abstractmethod
    def base_description(self) -> str: ...

    @property
    def description(self) -> str:
        return "TODO"

    @property
    def requires_cursor(self) -> bool:
        return False

    def _get_dep_keys(
        self, asset_key: AssetKey, asset_graph: BaseAssetGraph[BaseAssetNode]
    ) -> AbstractSet[AssetKey]:
        check_keys = asset_graph.get(asset_key).check_keys
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

    @property
    def name(self) -> str:
        return "ANY_DEPS_MATCH"

    def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:
        dep_results = []
        true_subset = context.get_empty_subset()

        for i, dep_key in enumerate(sorted(self._get_dep_keys(context.key, context.asset_graph))):
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition,
                    child_index=i,
                    candidate_subset=context.candidate_subset,
                )
            )
            dep_results.append(dep_result)
            true_subset = true_subset.compute_union(dep_result.true_subset)

        true_subset = context.candidate_subset.compute_intersection(true_subset)
        return AutomationResult(context, true_subset=true_subset, child_results=dep_results)


@whitelist_for_serdes
class AllDepsCondition(DepCondition):
    @property
    def base_description(self) -> str:
        return "All"

    @property
    def name(self) -> str:
        return "ALL_DEPS_MATCH"

    def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:
        dep_results = []
        true_subset = context.candidate_subset

        for i, dep_key in enumerate(sorted(self._get_dep_keys(context.key, context.asset_graph))):
            dep_condition = DepConditionWrapperCondition(dep_key=dep_key, operand=self.operand)
            dep_result = dep_condition.evaluate(
                context.for_child_condition(
                    child_condition=dep_condition,
                    child_index=i,
                    candidate_subset=context.candidate_subset,
                )
            )
            dep_results.append(dep_result)
            true_subset = true_subset.compute_intersection(dep_result.true_subset)

        return AutomationResult(context, true_subset=true_subset, child_results=dep_results)
