from abc import ABC, abstractproperty
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence

from .asset_subset import AssetSubset

if TYPE_CHECKING:
    from .asset_automation_evaluator import AssetAutomationConditionSnapshot, AutomationCondition


class AssetAutomationConditionCursorValue(ABC):
    """This class represents an arbitrary serialized value tracked by a particular AssetAutomationCondition."""

    @abstractproperty
    def max_storage_id(self) -> Optional[int]:
        """The maximum storage ID from the previous tick."""


class AssetAutomationConditionCursor(NamedTuple):
    condition_snapshot: "AssetAutomationConditionSnapshot"
    child_cursors: Sequence["AssetAutomationConditionCursor"]
    cursor_value: Optional[AssetAutomationConditionCursorValue]

    @property
    def max_storage_id(self) -> Optional[int]:
        return self.cursor_value.max_storage_id if self.cursor_value else None

    def for_child(self, child: "AutomationCondition") -> Optional["AssetAutomationConditionCursor"]:
        for child_cursor in self.child_cursors:
            if child_cursor.condition_snapshot == child.to_snapshot():
                return child_cursor
        return None


class GenericConditionCursorValue(
    AssetAutomationConditionCursorValue,
    NamedTuple(
        "_GenericConditionCursorValue",
        [
            ("max_storage_id", Optional[int]),
            ("previous_evaluation_timestamp", Optional[float]),
            ("subset", Optional[AssetSubset]),
        ],
    ),
):
    ...


class CronConditionCursorValue(
    AssetAutomationConditionCursorValue,
    NamedTuple(
        "_CronConditionCursor",
        [
            ("previous_evaluation_timestamp", Optional[float]),
            ("materialized_or_requested_subset", Optional[AssetSubset]),
        ],
    ),
):
    ...


class MissingConditionCursorValue(
    AssetAutomationConditionCursorValue,
    NamedTuple(
        "_MissingConditionCursorValue",
        [("materialized_or_requested_subset", Optional[AssetSubset])],
    ),
):
    ...
