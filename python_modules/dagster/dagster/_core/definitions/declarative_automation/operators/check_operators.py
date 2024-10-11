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
from dagster._core.definitions.declarative_automation.operators.dep_operators import (
    EntityMatchesCondition,
)
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


@record
class ChecksAutomationCondition(BuiltinAutomationCondition[AssetKey]):
    operand: AutomationCondition[AssetCheckKey]

    blocking_only: bool = False

    @property
    @abstractmethod
    def base_name(self) -> str: ...

    @property
    def name(self) -> str:
        name = self.base_name
        if self.blocking_only:
            name += "(blocking_only=True)"
        return name

    @property
    def requires_cursor(self) -> bool:
        return False

    def _get_check_keys(
        self, key: AssetKey, asset_graph: BaseAssetGraph[BaseAssetNode]
    ) -> AbstractSet[AssetCheckKey]:
        check_keys = asset_graph.get(key).check_keys
        if self.blocking_only:
            return {ck for ck in check_keys if asset_graph.get(ck).blocking}
        else:
            return check_keys


@whitelist_for_serdes
@record
class AnyChecksCondition(ChecksAutomationCondition):
    @property
    def base_name(self) -> str:
        return "ANY_CHECKS_MATCH"

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:
        check_results = []
        true_subset = context.get_empty_subset()

        for i, check_key in enumerate(
            sorted(self._get_check_keys(context.key, context.asset_graph))
        ):
            check_condition = EntityMatchesCondition(key=check_key, operand=self.operand)
            check_result = await check_condition.evaluate(
                context.for_child_condition(
                    child_condition=check_condition,
                    child_index=i,
                    candidate_subset=context.candidate_subset,
                )
            )
            check_results.append(check_result)
            true_subset = true_subset.compute_union(check_result.true_subset)

        true_subset = context.candidate_subset.compute_intersection(true_subset)
        return AutomationResult(context, true_subset=true_subset, child_results=check_results)


@whitelist_for_serdes
@record
class AllChecksCondition(ChecksAutomationCondition):
    @property
    def base_name(self) -> str:
        return "ALL_CHECKS_MATCH"

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:
        check_results = []
        true_subset = context.candidate_subset

        for i, check_key in enumerate(
            sorted(self._get_check_keys(context.key, context.asset_graph))
        ):
            check_condition = EntityMatchesCondition(key=check_key, operand=self.operand)
            check_result = await check_condition.evaluate(
                context.for_child_condition(
                    child_condition=check_condition,
                    child_index=i,
                    candidate_subset=context.candidate_subset,
                )
            )
            check_results.append(check_result)
            true_subset = true_subset.compute_intersection(check_result.true_subset)

        return AutomationResult(context, true_subset=true_subset, child_results=check_results)
