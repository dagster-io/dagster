import asyncio
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union

from dagster_shared.record import replace
from dagster_shared.serdes import whitelist_for_serdes
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
    BuiltinAutomationCondition,
    T_AutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators.utils import has_allow_ignore
from dagster._core.definitions.metadata import MetadataMapping
from dagster._core.definitions.metadata.metadata_value import FloatMetadataValue, IntMetadataValue
from dagster._record import copy, record

if TYPE_CHECKING:
    from dagster._core.definitions.asset_selection import AssetSelection


@record
class SinceConditionData:
    """Convenience class for manipulating metadata relevant to historical SinceCondition evaluations.
    Tracks the previous evaluation id and timestamp of the last evaluation where the trigger condition
    and reset conditions were true.
    """

    trigger_evaluation_id: Optional[int]
    trigger_timestamp: Optional[float]
    reset_evaluation_id: Optional[int]
    reset_timestamp: Optional[float]

    @staticmethod
    def from_metadata(metadata: Optional[MetadataMapping]) -> "SinceConditionData":
        def _get_int(key: str) -> Optional[int]:
            metadata_val = metadata.get(key, None) if metadata else None
            return metadata_val.value if isinstance(metadata_val, IntMetadataValue) else None

        def _get_float(key: str) -> Optional[float]:
            metadata_val = metadata.get(key, None) if metadata else None
            return metadata_val.value if isinstance(metadata_val, FloatMetadataValue) else None

        return SinceConditionData(
            trigger_evaluation_id=_get_int("trigger_evaluation_id"),
            trigger_timestamp=_get_float("trigger_timestamp"),
            reset_evaluation_id=_get_int("reset_evaluation_id"),
            reset_timestamp=_get_float("reset_timestamp"),
        )

    def to_metadata(self) -> Mapping[str, Union[IntMetadataValue, FloatMetadataValue]]:
        return dict(
            trigger_evaluation_id=IntMetadataValue(self.trigger_evaluation_id),
            trigger_timestamp=FloatMetadataValue(self.trigger_timestamp),
            reset_evaluation_id=IntMetadataValue(self.reset_evaluation_id),
            reset_timestamp=FloatMetadataValue(self.reset_timestamp),
        )

    def update(
        self,
        evaluation_id: int,
        timestamp: float,
        trigger_result: AutomationResult,
        reset_result: AutomationResult,
    ) -> "SinceConditionData":
        updated = self
        if not trigger_result.true_subset.is_empty:
            updated = replace(
                updated, trigger_evaluation_id=evaluation_id, trigger_timestamp=timestamp
            )
        if not reset_result.true_subset.is_empty:
            updated = replace(updated, reset_evaluation_id=evaluation_id, reset_timestamp=timestamp)
        return updated


@whitelist_for_serdes
@record
class SinceCondition(BuiltinAutomationCondition[T_EntityKey]):
    trigger_condition: AutomationCondition[T_EntityKey]
    reset_condition: AutomationCondition[T_EntityKey]

    @property
    def name(self) -> str:
        return "SINCE"

    @property
    def children(self) -> Sequence[AutomationCondition[T_EntityKey]]:
        return [self.trigger_condition, self.reset_condition]

    async def evaluate(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, context: AutomationContext[T_EntityKey]
    ) -> AutomationResult[T_EntityKey]:
        # must evaluate child condition over the entire subset to avoid missing state transitions
        child_candidate_subset = context.asset_graph_view.get_full_subset(key=context.key)

        # compute result for trigger and reset conditions
        trigger_result, reset_result = await asyncio.gather(
            *[
                context.for_child_condition(
                    self.trigger_condition,
                    child_indices=[0],
                    candidate_subset=child_candidate_subset,
                ).evaluate_async(),
                context.for_child_condition(
                    self.reset_condition,
                    child_indices=[1],
                    candidate_subset=child_candidate_subset,
                ).evaluate_async(),
            ]
        )

        # take the previous subset that this was true for
        true_subset = context.previous_true_subset or context.get_empty_subset()

        # add in any newly true trigger asset partitions
        true_subset = true_subset.compute_union(trigger_result.true_subset)
        # remove any newly true reset asset partitions
        true_subset = true_subset.compute_difference(reset_result.true_subset)

        # if anything changed since the previous evaluation, update the metadata
        condition_data = SinceConditionData.from_metadata(context.previous_metadata).update(
            context.evaluation_id,
            context.evaluation_time.timestamp(),
            trigger_result=trigger_result,
            reset_result=reset_result,
        )

        return AutomationResult(
            context=context,
            true_subset=true_subset,
            child_results=[trigger_result, reset_result],
            metadata=condition_data.to_metadata(),
        )

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
            else copy(
                self,
                trigger_condition=self.trigger_condition.replace(old, new),
                reset_condition=self.reset_condition.replace(old, new),
            )
        )

    @public
    def allow(self, selection: "AssetSelection") -> "SinceCondition":
        """Applies the ``.allow()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to allow.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            trigger_condition=self.trigger_condition.allow(selection)
            if has_allow_ignore(self.trigger_condition)
            else self.trigger_condition,
            reset_condition=self.reset_condition.allow(selection)
            if has_allow_ignore(self.reset_condition)
            else self.reset_condition,
        )

    @public
    def ignore(self, selection: "AssetSelection") -> "SinceCondition":
        """Applies the ``.ignore()`` method across all sub-conditions.

        This impacts any dep-related sub-conditions.

        Args:
            selection (AssetSelection): The selection to ignore.
        """
        from dagster._core.definitions.asset_selection import AssetSelection

        check.inst_param(selection, "selection", AssetSelection)
        return copy(
            self,
            trigger_condition=self.trigger_condition.ignore(selection)
            if has_allow_ignore(self.trigger_condition)
            else self.trigger_condition,
            reset_condition=self.reset_condition.ignore(selection)
            if has_allow_ignore(self.reset_condition)
            else self.reset_condition,
        )
