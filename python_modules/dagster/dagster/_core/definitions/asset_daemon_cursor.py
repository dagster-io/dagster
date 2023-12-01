import functools
from typing import Mapping, NamedTuple, Optional, Sequence

from dagster._core.definitions.events import AssetKey

from .asset_automation_condition_cursor import AssetAutomationConditionCursor
from .asset_automation_evaluator import ConditionEvaluation


class AssetDaemonAssetCursor(NamedTuple):
    """Convenience class to represent the state of an individual asset being handled by the daemon.
    In the future, this will be serialized as part of the cursor.
    """

    asset_key: AssetKey
    latest_evaluation: Optional[ConditionEvaluation]
    condition_cursor: AssetAutomationConditionCursor


class AssetDaemonCursor(NamedTuple):
    """State that's saved between reconciliation evaluations."""

    evaluation_id: int
    asset_cursors: Sequence[AssetDaemonAssetCursor]

    @functools.cached_property
    def asset_cursors_by_key(self) -> Mapping[AssetKey, AssetDaemonAssetCursor]:
        return {cursor.asset_key: cursor for cursor in self.asset_cursors}

    def get_asset_cursor(self, asset_key: AssetKey) -> Optional[AssetDaemonAssetCursor]:
        return self.asset_cursors_by_key.get(asset_key)

    def get_latest_evaluation(self, asset_key: AssetKey) -> Optional[ConditionEvaluation]:
        cursor = self.get_asset_cursor(asset_key)
        return cursor.latest_evaluation if cursor else None
