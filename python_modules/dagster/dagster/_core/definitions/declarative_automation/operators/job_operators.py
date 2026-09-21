import asyncio
from abc import abstractmethod
from collections.abc import Sequence
from typing import AbstractSet  # noqa: UP035

from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetJobKey, AssetKey
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators.dep_operators import (
    EntityMatchesCondition,
)
from dagster._core.definitions.declarative_automation.serialized_objects import OperatorType
from dagster._record import record


@record
class JobRootAssetsAutomationCondition(BuiltinAutomationCondition[AssetJobKey]):
    """Base for job-scoped conditions that aggregate a per-asset condition across the
    job's root assets (those with no in-job parents; downstream assets are inferred via
    lookahead). A job has no execution record of its own, so its condition is always
    expressed in terms of its assets (via EntityMatchesCondition).
    """

    operand: AutomationCondition[AssetKey]

    @property
    @abstractmethod
    def base_name(self) -> str: ...

    @property
    def name(self) -> str:
        return self.base_name

    @property
    def children(self) -> Sequence[AutomationCondition]:
        # `operand` is our nested condition. The framework finds a condition's nested
        # conditions by reading `children`, so it must be listed here.
        return [self.operand]

    @property
    def requires_cursor(self) -> bool:
        return False

    def _get_asset_keys(
        self, key: AssetJobKey, asset_graph: BaseAssetGraph[BaseAssetNode]
    ) -> AbstractSet[AssetKey]:
        """All asset keys belonging to this job."""
        return asset_graph.asset_keys_for_job(key.job_name)

    def _get_root_asset_keys(
        self, key: AssetJobKey, asset_graph: BaseAssetGraph[BaseAssetNode]
    ) -> AbstractSet[AssetKey]:
        """The job's root assets: those with no parents that are also in the job.

        Only roots are evaluated: downstream assets are pulled in via each asset
        condition's will_be_requested() lookahead within the same tick, so re-evaluating
        them at the job level would be redundant.
        """
        job_asset_keys = self._get_asset_keys(key, asset_graph)
        return {
            asset_key
            for asset_key in job_asset_keys
            if not (asset_graph.get(asset_key).parent_entity_keys & job_asset_keys)
        }

    def _child_for_asset_key(
        self, context: AutomationContext[AssetJobKey], index: int, asset_key: AssetKey
    ) -> AutomationContext:
        child_condition = EntityMatchesCondition[AssetJobKey, AssetKey](
            key=asset_key, operand=self.operand
        )
        return context.for_child_condition(
            child_condition=child_condition,
            child_indices=[None, index],
            candidate_subset=context.candidate_subset,
        )


@whitelist_for_serdes
@record
class AnyJobRootAssetsMatchCondition(JobRootAssetsAutomationCondition):
    @property
    def base_name(self) -> str:
        return "ANY_JOB_ROOT_ASSETS_MATCH"

    @property
    def operator_type(self) -> OperatorType:
        return "or"

    async def evaluate(  # ty: ignore[invalid-method-override]
        self, context: AutomationContext[AssetJobKey]
    ) -> AutomationResult[AssetJobKey]:
        target_keys = sorted(self._get_root_asset_keys(context.key, context.asset_graph))
        asset_results = await asyncio.gather(
            *(
                self._child_for_asset_key(context, i, asset_key).evaluate_async()
                for i, asset_key in enumerate(target_keys)
            )
        )

        true_subset = context.get_empty_subset()
        for asset_result in asset_results:
            true_subset = true_subset.compute_union(asset_result.true_subset)
        true_subset = context.candidate_subset.compute_intersection(true_subset)

        return AutomationResult(context, true_subset=true_subset, child_results=asset_results)


@whitelist_for_serdes
@record
class AllJobRootAssetsMatchCondition(JobRootAssetsAutomationCondition):
    @property
    def base_name(self) -> str:
        return "ALL_JOB_ROOT_ASSETS_MATCH"

    @property
    def operator_type(self) -> OperatorType:
        return "and"

    async def evaluate(  # ty: ignore[invalid-method-override]
        self, context: AutomationContext[AssetJobKey]
    ) -> AutomationResult[AssetJobKey]:
        target_keys = sorted(self._get_root_asset_keys(context.key, context.asset_graph))
        asset_results = await asyncio.gather(
            *(
                self._child_for_asset_key(context, i, asset_key).evaluate_async()
                for i, asset_key in enumerate(target_keys)
            )
        )

        true_subset = context.candidate_subset
        for asset_result in asset_results:
            true_subset = true_subset.compute_intersection(asset_result.true_subset)

        return AutomationResult(context, true_subset=true_subset, child_results=asset_results)


def contains_job_root_assets_condition(condition: AutomationCondition) -> bool:
    """Whether any node in the condition tree is a JobRootAssetsAutomationCondition."""
    if isinstance(condition, JobRootAssetsAutomationCondition):
        return True
    return any(contains_job_root_assets_condition(child) for child in condition.children)
