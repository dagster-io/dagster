from abc import ABC, abstractproperty
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional

from .asset_subset import AssetSubset

if TYPE_CHECKING:
    from .asset_automation_evaluator import AssetAutomationConditionSnapshot


class AssetAutomationConditionCursorValue(ABC):
    """This class represents an arbitrary serialized value tracked by a particular AssetAutomationCondition."""

    @abstractproperty
    def max_storage_id(self) -> Optional[int]:
        """The maximum storage ID from the previous tick."""


class AssetAutomationConditionCursor(NamedTuple):
    children: Mapping["AssetAutomationConditionSnapshot", "AssetAutomationConditionCursor"]
    cursor_value: AssetAutomationConditionCursorValue


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
