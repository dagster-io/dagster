from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence

from dagster._serdes.serdes import PackableValue

if TYPE_CHECKING:
    from .asset_automation_evaluator import AssetAutomationConditionSnapshot, AutomationCondition


class AssetAutomationConditionCursor(NamedTuple):
    condition_snapshot: "AssetAutomationConditionSnapshot"
    max_storage_id: Optional[int]
    extras: Mapping[str, PackableValue]
    child_cursors: Sequence["AssetAutomationConditionCursor"]

    def for_child(self, child: "AutomationCondition") -> Optional["AssetAutomationConditionCursor"]:
        for child_cursor in self.child_cursors:
            if child_cursor.condition_snapshot == child.to_snapshot():
                return child_cursor
        return None
