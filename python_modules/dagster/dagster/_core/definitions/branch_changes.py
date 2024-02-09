from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.definitions.asset_graph import AssetGraph
    from dagster._core.definitions.events import (
        AssetKey,
    )
    from dagster._core.instance import DagsterInstance


class ChangeReason(Enum):
    NEW = "NEW"
    CODE_VERSION = "CODE_VERSION"
    INPUTS = "INPUTS"


class BranchChangeResolver:
    _instance: "DagsterInstance"
    _branch_asset_graph: Optional["AssetGraph"]
    _branch_asset_graph_load_fn: Optional[Callable[[], "AssetGraph"]]
    _parent_asset_graph: Optional["AssetGraph"]

    def __init__(
        self,
        instance: "DagsterInstance",
        branch_asset_graph: Union["AssetGraph", Callable[[], "AssetGraph"]],
    ):
        from dagster._core.definitions.asset_graph import AssetGraph

        self._instance = instance
        if isinstance(branch_asset_graph, AssetGraph):
            self._branch_asset_graph = branch_asset_graph
            self._branch_asset_graph_load_fn = None
        else:
            self._branch_asset_graph = None
            self._branch_asset_graph_load_fn = branch_asset_graph

        if self._is_branch_deployment():
            self._parent_asset_graph = self._get_parent_deployment_asset_graph()
        else:
            self._changed_status_by_asset_key = {}

    def _is_branch_deployment(self) -> bool:
        """Determines if the current deployment is a branch deployment."""
        if self._instance.cloud_deployment is not None:
            return self._instance.cloud_deployment.is_branch_deployment
        return False

    def _get_parent_deployment_asset_graph(self):
        if self._instance.cloud_deployment is not None:
            parent_deployment = self._instance.cloud_deployment.compute_parent_deployment()
        return None

    def _compare_parent_and_branch_assets(self, asset_key: "AssetKey") -> Sequence[ChangeReason]:
        """Computes the diff between a branch deployment asset and the
        corresponding parent deployment asset.
        """
        if not self._is_branch_deployment():
            return []

        if self._parent_asset_graph is None:
            # TODO - this might indicate that the entire asset graph is new, and thus should
            # return ChangeReason.NEW. This will depend on how the parent asset graph is fetched.
            return []

        if asset_key not in self._parent_asset_graph.all_asset_keys:
            return [ChangeReason.NEW]

        changes = []
        if self.branch_asset_graph.get_code_version(
            asset_key
        ) != self._parent_asset_graph.get_code_version(asset_key):
            changes.append(ChangeReason.CODE_VERSION)

        if self.branch_asset_graph.get_parents(asset_key) != self._parent_asset_graph.get_parents(
            asset_key
        ):
            changes.append(ChangeReason.INPUTS)

        return changes

    def is_changed_in_branch(self, asset_key: "AssetKey") -> bool:
        """Returns whether the given asset has been changed in the branch deployment."""
        # TODO - unclear if this method is really necessary. Consider removing.
        return len(self._compare_parent_and_branch_assets(asset_key)) > 0

    def get_changes_for_asset(self, asset_key: "AssetKey") -> Sequence[ChangeReason]:
        """Returns list of ChangeReasons for asset_key as compared to the parent deployment."""
        return self._compare_parent_and_branch_assets(asset_key)

    @property
    def branch_asset_graph(self) -> "AssetGraph":
        if self._branch_asset_graph is None:
            self._branch_asset_graph = check.not_none(self._branch_asset_graph_load_fn)()
        return self._branch_asset_graph
