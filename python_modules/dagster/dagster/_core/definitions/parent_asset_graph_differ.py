from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union

import dagster._check as check
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.workspace.context import BaseWorkspaceRequestContext

if TYPE_CHECKING:
    from dagster._core.definitions.events import (
        AssetKey,
    )


class ChangeReason(Enum):
    NEW = "NEW"
    CODE_VERSION = "CODE_VERSION"
    INPUTS = "INPUTS"


class ParentAssetGraphDiffer:
    """Given two asset graphs, parent_asset_graph and branch_asset_graph, we can compute how the
    assets in branch_asset_graph have changed with respect to parent_asset_graph. The ChangeReason
    enum contains the list of potential changes an asset can undergo.
    """

    _branch_asset_graph: Optional["ExternalAssetGraph"]
    _branch_asset_graph_load_fn: Optional[Callable[[], "ExternalAssetGraph"]]
    _parent_asset_graph: Optional["ExternalAssetGraph"]
    _parent_asset_graph_load_fn: Optional[Callable[[], "ExternalAssetGraph"]]

    def __init__(
        self,
        # repository_name: str,
        branch_asset_graph: Union["ExternalAssetGraph", Callable[[], "ExternalAssetGraph"]],
        parent_asset_graph: Optional[
            Union["ExternalAssetGraph", Callable[[], "ExternalAssetGraph"]]
        ] = None,
    ):
        if parent_asset_graph is None:
            # if parent_asset_graph is None, we are not in a branch deployment.
            self._parent_asset_graph = None
            self._parent_asset_graph_load_fn = None
            self._is_branch_deployment = False
        elif isinstance(parent_asset_graph, ExternalAssetGraph):
            self._parent_asset_graph = parent_asset_graph
            self._parent_asset_graph_load_fn = None
            self._is_branch_deployment = True
        else:
            self._parent_asset_graph = None
            self._parent_asset_graph_load_fn = parent_asset_graph
            self._is_branch_deployment = True

        if isinstance(branch_asset_graph, ExternalAssetGraph):
            self._branch_asset_graph = branch_asset_graph
            self._branch_asset_graph_load_fn = None
        else:
            self._branch_asset_graph = None
            self._branch_asset_graph_load_fn = branch_asset_graph

    @classmethod
    def from_workspaces(
        cls,
        # repository_name: str,
        branch_workspace: BaseWorkspaceRequestContext,
        parent_workspace: Optional[BaseWorkspaceRequestContext] = None,
    ) -> Optional["ParentAssetGraphDiffer"]:
        if parent_workspace is not None:
            return ParentAssetGraphDiffer(
                branch_asset_graph=lambda: ExternalAssetGraph.from_workspace(branch_workspace),
                parent_asset_graph=lambda: ExternalAssetGraph.from_workspace(parent_workspace),
                # repository_name=repository_name
            )

    def _compare_parent_and_branch_assets(self, asset_key: "AssetKey") -> Sequence[ChangeReason]:
        """Computes the diff between a branch deployment asset and the
        corresponding parent deployment asset.
        """
        if not self._is_branch_deployment:
            return []

        if self.parent_asset_graph is None:
            # TODO - this might indicate that the entire asset graph is new, and thus should
            # return ChangeReason.NEW. This will depend on how the parent asset graph is fetched.
            return []

        if asset_key not in self.parent_asset_graph.all_asset_keys:
            return [ChangeReason.NEW]

        changes = []
        if self.branch_asset_graph.get_code_version(
            asset_key
        ) != self.parent_asset_graph.get_code_version(asset_key):
            changes.append(ChangeReason.CODE_VERSION)

        if self.branch_asset_graph.get_parents(asset_key) != self.parent_asset_graph.get_parents(
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
    def branch_asset_graph(self) -> "ExternalAssetGraph":
        if self._branch_asset_graph is None:
            self._branch_asset_graph = check.not_none(self._branch_asset_graph_load_fn)()
        return self._branch_asset_graph

    @property
    def parent_asset_graph(self) -> Optional["ExternalAssetGraph"]:
        if self._parent_asset_graph is None and self._parent_asset_graph_load_fn is not None:
            self._parent_asset_graph = self._parent_asset_graph_load_fn()
        return self._parent_asset_graph
