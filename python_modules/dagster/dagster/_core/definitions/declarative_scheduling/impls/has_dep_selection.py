from typing import AbstractSet, Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._model import DagsterModel
from dagster._utils.cached_method import cached_method


class IHasDepSelection(DagsterModel):
    """Interface for all SchedulingConditions which contain a dep_selection."""

    dep_selection: Optional[AssetSelection] = None

    @cached_method
    def get_dep_keys(
        self, *, asset_key: AssetKey, asset_graph: BaseAssetGraph
    ) -> AbstractSet[AssetKey]:
        selection = AssetSelection.keys(asset_key).upstream(depth=1, include_self=False)
        if self.dep_selection:
            selection &= self.dep_selection
        return selection.resolve(asset_graph)

    def __hash__(self) -> int:
        return id(self)
