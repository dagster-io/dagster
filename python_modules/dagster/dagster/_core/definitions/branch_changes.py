from typing import (
    TYPE_CHECKING,
    Callable,
    Mapping,
    Optional,
    Union,
)

import dagster._check as check

if TYPE_CHECKING:
    from dagster._core.definitions.asset_graph import AssetGraph
    from dagster._core.definitions.events import (
        AssetKey,
    )
    from dagster._core.instance import DagsterInstance


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
        from dagster._core.definitions.asset_graph import AssetGraph, AssetKey

        self._instance = instance
        if isinstance(branch_asset_graph, AssetGraph):
            self._branch_asset_graph = branch_asset_graph
            self._branch_asset_graph_load_fn = None
        else:
            self._branch_asset_graph = None
            self._branch_asset_graph_load_fn = branch_asset_graph

        if self._is_branch_deployment():
            self._parent_asset_graph = self._get_parent_deployment_asset_graph()
            self._changed_status_by_asset_key: Mapping[
                AssetKey, bool
            ] = self._compare_parent_and_branch_asset_graphs()
        else:
            self._changed_status_by_asset_key = {}

    def _is_branch_deployment(self) -> bool:
        """Determines if the current deployment is a branch deployment."""
        # TODO - implement.
        return False

    def _get_parent_deployment_asset_graph(self):
        # TODO - implement. For now we can override in the test suite
        return None

    def _compare_parent_and_branch_asset_graphs(self) -> Mapping["AssetKey", bool]:
        """Computes the diff between a branch deployment asset graph and the
        corresponding parent deployment asset graph.

        TODO - this is a really rough impl right now. Will get better later
        """
        if self._parent_asset_graph is None:
            return {}

        changes = {}
        for asset_key in self.branch_asset_graph.all_asset_keys:
            if asset_key in self._parent_asset_graph.all_asset_keys:
                if self.branch_asset_graph.get_code_version(
                    asset_key
                ) != self._parent_asset_graph.get_code_version(
                    asset_key
                ) or self.branch_asset_graph.get_parents(
                    asset_key
                ) != self._parent_asset_graph.get_parents(asset_key):
                    changes[asset_key] = True
                else:
                    changes[asset_key] = False
            else:
                changes[asset_key] = True

        return changes

    def is_changed_in_branch(self, asset_key: "AssetKey") -> bool:
        """Returns whether the given asset has been changed in the branch deployment."""
        return self._changed_status_by_asset_key.get(asset_key, False)

    @property
    def branch_asset_graph(self) -> "AssetGraph":
        if self._branch_asset_graph is None:
            self._branch_asset_graph = check.not_none(self._branch_asset_graph_load_fn)()
        return self._branch_asset_graph
