from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, AbstractSet, Any, Generic, Optional, Union  # noqa: UP035

from dagster_shared.serdes import whitelist_for_serdes
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import public
from dagster._core.asset_graph_view.asset_graph_view import U_EntityKey
from dagster._core.definitions.asset_key import AssetKey, T_EntityKey
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
    T_AutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.serialized_objects import OperatorType
from dagster._record import copy, record
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from dagster._core.definitions.asset_selection import AssetSelection


@whitelist_for_serdes
@record
class EntityMatchesCondition(
    BuiltinAutomationCondition[T_EntityKey], Generic[T_EntityKey, U_EntityKey]
):
    key: U_EntityKey
    operand: AutomationCondition[U_EntityKey]

    @property
    def name(self) -> str:
        return self.key.to_user_string()

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.operand]

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        # if the key we're mapping to is a child of the key we're mapping from and is not
        # self-dependent, use the downstream mapping function, otherwise use upstream
        if (
            self.key in context.asset_graph.get(context.key).child_entity_keys
            and self.key != context.key
        ):
            directions = ("down", "up")
        else:
            directions = ("up", "down")

        to_candidate_subset = context.candidate_subset.compute_mapped_subset(
            self.key, direction=directions[0]
        )
        to_context = context.for_child_condition(
            child_condition=self.operand,
            child_indices=[0],
            candidate_subset=to_candidate_subset,
        )

        to_result = await to_context.evaluate_async()

        true_subset = to_result.true_subset.compute_mapped_subset(
            context.key, direction=directions[1]
        )
        return AutomationResult(context=context, true_subset=true_subset, child_results=[to_result])

    @public
    def replace(
        self, old: Union[AutomationCondition, str], new: T_AutomationCondition
    ) -> Union[Self, T_AutomationCondition]:
        """Replaces all instances of ``old`` across any sub-conditions with ``new``.

        If ``old`` is a string, then conditions with a label or name matching
        that string will be replaced.

        Args:
            old (Union[AutomationCondition, str]): The condition to replace.
            new (AutomationCondition): The condition to replace with.
        """
        return (
            new
            if old in [self, self.name, self.get_label()]
            else copy(self, operand=self.operand.replace(old, new))
        )


@record
class DepsAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    operand: AutomationCondition

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
        if self.allow_selection is not None:
            props.append(f"allow_selection={self.allow_selection}")
        if self.ignore_selection is not None:
            props.append(f"ignore_selection={self.ignore_selection}")

        if props:
            name += f"({','.join(props)})"
        return name

    @property
    def children(self) -> Sequence[AutomationCondition]:
        return [self.operand]

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

    @public
    def allow(self, selection: "AssetSelection") -> "DepsAutomationCondition":
        """Returns a copy of this condition that will only consider dependencies within the provided
        AssetSelection.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        allow_selection = (
            selection if self.allow_selection is None else selection | self.allow_selection
        )
        return copy(self, allow_selection=allow_selection)

    @public
    def ignore(self, selection: "AssetSelection") -> "DepsAutomationCondition":
        """Returns a copy of this condition that will ignore dependencies within the provided
        AssetSelection.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        ignore_selection = (
            selection if self.ignore_selection is None else selection | self.ignore_selection
        )
        return copy(self, ignore_selection=ignore_selection)

    def _get_dep_keys(
        self, key: T_EntityKey, asset_graph: BaseAssetGraph[BaseAssetNode]
    ) -> AbstractSet[AssetKey]:
        dep_keys = asset_graph.get(key).parent_entity_keys
        if self.allow_selection is not None:
            dep_keys &= self.allow_selection.resolve(asset_graph, allow_missing=True)
        if self.ignore_selection is not None:
            dep_keys -= self.ignore_selection.resolve(asset_graph, allow_missing=True)
        return dep_keys

    @public
    def replace(
        self, old: Union[AutomationCondition, str], new: T_AutomationCondition
    ) -> Union[Self, T_AutomationCondition]:
        """Replaces all instances of ``old`` across any sub-conditions with ``new``.

        If ``old`` is a string, then conditions with a label or name matching
        that string will be replaced.

        Args:
            old (Union[AutomationCondition, str]): The condition to replace.
            new (AutomationCondition): The condition to replace with.
        """
        return (
            new
            if old in [self, self.name, self.get_label()]
            else copy(self, operand=self.operand.replace(old, new))
        )


@whitelist_for_serdes
class AnyDepsCondition(DepsAutomationCondition[T_EntityKey]):
    @property
    def base_name(self) -> str:
        return "ANY_DEPS_MATCH"

    @property
    def operator_type(self) -> OperatorType:
        return "or"

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        dep_results = []
        true_subset = context.get_empty_subset()

        for i, dep_key in enumerate(sorted(self._get_dep_keys(context.key, context.asset_graph))):
            dep_result = await context.for_child_condition(
                child_condition=EntityMatchesCondition(key=dep_key, operand=self.operand),
                child_indices=[  # Prefer a non-indexed ID in case asset keys move around, but fall back to the indexed one for back-compat
                    None,
                    i,
                ],
                candidate_subset=context.candidate_subset,
            ).evaluate_async()
            dep_results.append(dep_result)
            true_subset = true_subset.compute_union(dep_result.true_subset)

        true_subset = context.candidate_subset.compute_intersection(true_subset)
        return AutomationResult(context, true_subset=true_subset, child_results=dep_results)


@whitelist_for_serdes
class AllDepsCondition(DepsAutomationCondition[T_EntityKey]):
    @property
    def base_name(self) -> str:
        return "ALL_DEPS_MATCH"

    @property
    def operator_type(self) -> OperatorType:
        return "and"

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        dep_results = []
        true_subset = context.candidate_subset

        for i, dep_key in enumerate(sorted(self._get_dep_keys(context.key, context.asset_graph))):
            dep_result = await context.for_child_condition(
                child_condition=EntityMatchesCondition(key=dep_key, operand=self.operand),
                child_indices=[  # Prefer a non-indexed ID in case asset keys move around, but fall back to the indexed one for back-compat
                    None,
                    i,
                ],
                candidate_subset=context.candidate_subset,
            ).evaluate_async()
            dep_results.append(dep_result)
            true_subset = true_subset.compute_intersection(dep_result.true_subset)

        return AutomationResult(context, true_subset=true_subset, child_results=dep_results)
