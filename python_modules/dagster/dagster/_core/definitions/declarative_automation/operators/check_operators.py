import asyncio
from abc import abstractmethod
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, Sequence  # noqa: UP035

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
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
from dagster._record import copy, record
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from dagster._core.definitions.asset_selection import AssetSelection


@record
class ChecksAutomationCondition(BuiltinAutomationCondition[AssetKey]):
    operand: AutomationCondition[AssetCheckKey]

    blocking_only: bool = False
    # Should be AssetSelection, but this causes circular reference issues
    allow_selection: Optional[Any] = None
    ignore_selection: Optional[Any] = None

    @property
    @abstractmethod
    def base_name(self) -> str: ...

    @property
    def name(self) -> str:
        name = self.base_name
        props = []
        if self.blocking_only:
            props.append("blocking_only=True")
        if self.allow_selection is not None:
            props.append(f"allow_selection={self.allow_selection}")
        if self.ignore_selection is not None:
            props.append(f"ignore_selection={self.ignore_selection}")

        if props:
            name += f"({','.join(props)})"
        return name

    @property
    def requires_cursor(self) -> bool:
        return False

    def get_node_unique_id(self, *, parent_unique_id: Optional[str], index: Optional[int]) -> str:
        """Ignore allow_selection / ignore_selection for the cursor hash."""
        parts = [str(parent_unique_id), str(index), self.base_name]
        return non_secure_md5_hash_str("".join(parts).encode())

    def get_backcompat_node_unique_ids(
        self, *, parent_unique_id: Optional[str] = None, index: Optional[int] = None
    ) -> Sequence[str]:
        # backcompat for previous cursors where the allow/ignore selection influenced the hash
        return [super().get_node_unique_id(parent_unique_id=parent_unique_id, index=index)]

    def allow(self, selection: "AssetSelection") -> "ChecksAutomationCondition":
        """Returns a copy of this condition that will only consider dependencies within the provided
        AssetSelection.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        allow_selection = (
            selection if self.allow_selection is None else selection | self.allow_selection
        )
        return copy(self, allow_selection=allow_selection)

    def ignore(self, selection: "AssetSelection") -> "ChecksAutomationCondition":
        """Returns a copy of this condition that will ignore dependencies within the provided
        AssetSelection.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        ignore_selection = (
            selection if self.ignore_selection is None else selection | self.ignore_selection
        )
        return copy(self, ignore_selection=ignore_selection)

    def _get_check_keys(
        self, key: AssetKey, asset_graph: BaseAssetGraph[BaseAssetNode]
    ) -> AbstractSet[AssetCheckKey]:
        check_keys = asset_graph.get(key).check_keys
        if self.blocking_only:
            check_keys = {ck for ck in check_keys if asset_graph.get(ck).blocking}
        if self.allow_selection is not None:
            check_keys &= self.allow_selection.resolve_checks(asset_graph)
        if self.ignore_selection is not None:
            check_keys -= self.ignore_selection.resolve_checks(asset_graph)

        return check_keys


@whitelist_for_serdes
@record
class AnyChecksCondition(ChecksAutomationCondition):
    @property
    def base_name(self) -> str:
        return "ANY_CHECKS_MATCH"

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        true_subset = context.get_empty_subset()

        coroutines = [
            context.for_child_condition(
                child_condition=EntityMatchesCondition(key=check_key, operand=self.operand),
                child_indices=[
                    None,
                    i,
                ],  # Prefer a non-indexed ID in case asset keys move around, but fall back to the indexed one for back-compat
                candidate_subset=context.candidate_subset,
            ).evaluate_async()
            for i, check_key in enumerate(
                sorted(self._get_check_keys(context.key, context.asset_graph))
            )
        ]

        check_results = await asyncio.gather(*coroutines)
        for check_result in check_results:
            true_subset = true_subset.compute_union(check_result.true_subset)

        true_subset = context.candidate_subset.compute_intersection(true_subset)
        return AutomationResult(context, true_subset=true_subset, child_results=check_results)


@whitelist_for_serdes
@record
class AllChecksCondition(ChecksAutomationCondition):
    @property
    def base_name(self) -> str:
        return "ALL_CHECKS_MATCH"

    async def evaluate(self, context: AutomationContext[AssetKey]) -> AutomationResult[AssetKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        check_results = []
        true_subset = context.candidate_subset

        for i, check_key in enumerate(
            sorted(self._get_check_keys(context.key, context.asset_graph))
        ):
            check_result = await context.for_child_condition(
                child_condition=EntityMatchesCondition(key=check_key, operand=self.operand),
                child_indices=[
                    None,
                    i,
                ],  # Prefer a non-indexed ID in case asset keys move around, but fall back to the indexed one for back-compat
                candidate_subset=context.candidate_subset,
            ).evaluate_async()
            check_results.append(check_result)
            true_subset = true_subset.compute_intersection(check_result.true_subset)

        return AutomationResult(context, true_subset=true_subset, child_results=check_results)
