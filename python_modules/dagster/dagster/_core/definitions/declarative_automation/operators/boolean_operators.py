import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING, Union

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators.utils import has_allow_ignore
from dagster._record import copy, record

if TYPE_CHECKING:
    from dagster._core.definitions.asset_selection import AssetSelection


@whitelist_for_serdes(storage_name="AndAssetCondition")
@record
class AndAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """This class represents the condition that all of its children evaluate to true."""

    operands: Sequence[AutomationCondition[T_EntityKey]]

    @property
    def description(self) -> str:
        return "All of"

    @property
    def name(self) -> str:
        return "AND"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return self.operands

    @property
    def requires_cursor(self) -> bool:
        return False

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        child_results: list[AutomationResult] = []
        true_subset = context.candidate_subset
        for i, child in enumerate(self.children):
            child_result = await context.for_child_condition(
                child_condition=child,
                child_indices=[i],
                candidate_subset=true_subset,
            ).evaluate_async()
            child_results.append(child_result)
            true_subset = true_subset.compute_intersection(child_result.true_subset)
        return AutomationResult(context, true_subset, child_results=child_results)

    def without(self, condition: AutomationCondition) -> "AndAutomationCondition":
        """Returns a copy of this condition without the specified child condition."""
        check.param_invariant(
            condition in self.operands, "condition", "Condition not found in operands"
        )
        operands = [child for child in self.operands if child != condition]
        if len(operands) < 2:
            check.failed("Cannot have fewer than 2 operands in an AndAutomationCondition")
        return copy(self, operands=[child for child in self.operands if child != condition])

    @public
    def replace(
        self, old: Union[AutomationCondition, str], new: AutomationCondition
    ) -> AutomationCondition:
        """Replaces all instances of ``old`` across any sub-conditions with ``new``.

        If ``old`` is a string, then conditions with a label matching
        that string will be replaced.

        Args:
            old (Union[AutomationCondition, str]): The condition to replace.
            new (AutomationCondition): The condition to replace with.
        """
        return (
            new
            if old in [self, self.get_label()]
            else copy(self, operands=[child.replace(old, new) for child in self.operands])
        )

    @public
    def allow(self, selection: "AssetSelection") -> "AndAutomationCondition":
        """Applies the ``.allow()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to allow.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            operands=[
                child.allow(selection) if has_allow_ignore(child) else child
                for child in self.operands
            ],
        )

    @public
    def ignore(self, selection: "AssetSelection") -> "AndAutomationCondition":
        """Applies the ``.ignore()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to ignore.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            operands=[
                child.ignore(selection) if has_allow_ignore(child) else child
                for child in self.operands
            ],
        )


@whitelist_for_serdes(storage_name="OrAssetCondition")
@record
class OrAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """This class represents the condition that any of its children evaluate to true."""

    operands: Sequence[AutomationCondition[T_EntityKey]]

    @property
    def description(self) -> str:
        return "Any of"

    @property
    def name(self) -> str:
        return "OR"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return self.operands

    @property
    def requires_cursor(self) -> bool:
        return False

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        true_subset = context.get_empty_subset()

        coroutines = [
            context.for_child_condition(
                child_condition=child,
                child_indices=[i],
                candidate_subset=context.candidate_subset,
            ).evaluate_async()
            for i, child in enumerate(self.children)
        ]

        child_results = await asyncio.gather(*coroutines)
        for child_result in child_results:
            true_subset = true_subset.compute_union(child_result.true_subset)

        return AutomationResult(context, true_subset, child_results=child_results)

    @public
    def replace(
        self, old: Union[AutomationCondition, str], new: AutomationCondition
    ) -> AutomationCondition:
        """Replaces all instances of ``old`` across any sub-conditions with ``new``.

        If ``old`` is a string, then conditions with a label matching
        that string will be replaced.

        Args:
            old (Union[AutomationCondition, str]): The condition to replace.
            new (AutomationCondition): The condition to replace with.
        """
        return (
            new
            if old in [self, self.get_label()]
            else copy(self, operands=[child.replace(old, new) for child in self.operands])
        )

    @public
    def allow(self, selection: "AssetSelection") -> "OrAutomationCondition":
        """Applies the ``.allow()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to allow.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            operands=[
                child.allow(selection) if has_allow_ignore(child) else child
                for child in self.operands
            ],
        )

    @public
    def ignore(self, selection: "AssetSelection") -> "OrAutomationCondition":
        """Applies the ``.ignore()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to ignore.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            operands=[
                child.ignore(selection) if has_allow_ignore(child) else child
                for child in self.operands
            ],
        )


@whitelist_for_serdes(storage_name="NotAssetCondition")
@record
class NotAutomationCondition(BuiltinAutomationCondition[T_EntityKey]):
    """This class represents the condition that none of its children evaluate to true."""

    operand: AutomationCondition[T_EntityKey]

    @property
    def description(self) -> str:
        return "Not"

    @property
    def name(self) -> str:
        return "NOT"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.operand]

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        child_result = await context.for_child_condition(
            child_condition=self.operand,
            child_indices=[0],
            candidate_subset=context.candidate_subset,
        ).evaluate_async()
        true_subset = context.candidate_subset.compute_difference(child_result.true_subset)

        return AutomationResult(context, true_subset, child_results=[child_result])

    @public
    def replace(
        self, old: Union[AutomationCondition, str], new: AutomationCondition
    ) -> AutomationCondition:
        """Replaces all instances of ``old`` across any sub-conditions with ``new``.

        If ``old`` is a string, then conditions with a label matching
        that string will be replaced.

        Args:
            old (Union[AutomationCondition, str]): The condition to replace.
            new (AutomationCondition): The condition to replace with.
        """
        return (
            new
            if old in [self, self.get_label()]
            else copy(self, operand=self.operand.replace(old, new))
        )

    @public
    def allow(self, selection: "AssetSelection") -> "NotAutomationCondition":
        """Applies the ``.allow()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to allow.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            operand=self.operand.allow(selection)
            if has_allow_ignore(self.operand)
            else self.operand,
        )

    @public
    def ignore(self, selection: "AssetSelection") -> "NotAutomationCondition":
        """Applies the ``.ignore()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to ignore.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            operand=self.operand.ignore(selection)
            if has_allow_ignore(self.operand)
            else self.operand,
        )
