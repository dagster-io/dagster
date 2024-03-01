from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union

import dagster._check as check
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.host_representation import ExternalRepository
from dagster._core.workspace.context import BaseWorkspaceRequestContext

if TYPE_CHECKING:
    from dagster._core.definitions.events import (
        AssetKey,
    )


class ChangeReason(Enum):
    NEW = "NEW"
    CODE_VERSION = "CODE_VERSION"
    INPUTS = "INPUTS"


def _get_external_repo_from_context(
    context: BaseWorkspaceRequestContext, code_location_name: str, repository_name: str
) -> Optional[ExternalRepository]:
    """Returns the ExternalRepository specified by the code location name and repository name
    for the provided workspace context. If the repository doesn't exist, return None.
    """
    if context.has_code_location(code_location_name):
        cl = context.get_code_location(code_location_name)
        if cl.has_repository(repository_name):
            return cl.get_repository(repository_name)


class AssetGraphDiffer:
    """Given two asset graphs, base_asset_graph and branch_asset_graph, we can compute how the
    assets in branch_asset_graph have changed with respect to base_asset_graph. The ChangeReason
    enum contains the list of potential changes an asset can undergo. If the base_asset_graph is None,
    this indicates that the branch_asset_graph does not yet exist in the base deployment. In this case
    we will consider every asset New.
    """

    _branch_asset_graph: Optional["ExternalAssetGraph"]
    _branch_asset_graph_load_fn: Optional[Callable[[], "ExternalAssetGraph"]]
    _base_asset_graph: Optional["ExternalAssetGraph"]
    _base_asset_graph_load_fn: Optional[Callable[[], "ExternalAssetGraph"]]

    def __init__(
        self,
        branch_asset_graph: Union["ExternalAssetGraph", Callable[[], "ExternalAssetGraph"]],
        base_asset_graph: Optional[
            Union["ExternalAssetGraph", Callable[[], "ExternalAssetGraph"]]
        ] = None,
    ):
        if base_asset_graph is None:
            # if base_asset_graph is None, then the asset graph in the branch deployment does not exist
            # in the base deployment
            self._base_asset_graph = None
            self._base_asset_graph_load_fn = None
        elif isinstance(base_asset_graph, ExternalAssetGraph):
            self._base_asset_graph = base_asset_graph
            self._base_asset_graph_load_fn = None
        else:
            self._base_asset_graph = None
            self._base_asset_graph_load_fn = base_asset_graph

        if isinstance(branch_asset_graph, ExternalAssetGraph):
            self._branch_asset_graph = branch_asset_graph
            self._branch_asset_graph_load_fn = None
        else:
            self._branch_asset_graph = None
            self._branch_asset_graph_load_fn = branch_asset_graph

    @classmethod
    def from_external_repositories(
        cls,
        code_location_name: str,
        repository_name: str,
        branch_workspace: BaseWorkspaceRequestContext,
        base_workspace: BaseWorkspaceRequestContext,
    ) -> "AssetGraphDiffer":
        """Constructs an AssetGraphDiffer for a particular repository in a code location for two
        deployment workspaces, the base deployment and the branch deployment.

        We cannot make ExternalAssetGraphs directly from the workspaces because if multiple code locations
        use the same asset key, those asset keys will override each other in the dictionaries the ExternalAssetGraph
        creates (see from_repository_handles_and_external_asset_nodes in ExternalAssetGraph). We need to ensure
        that we are comparing assets in the same code location and repository, so we need to make the
        ExternalAssetGraph from an ExternalRepository to ensure that there are no duplicate asset keys
        that could override each other.
        """
        check.inst_param(branch_workspace, "branch_workspace", BaseWorkspaceRequestContext)
        check.inst_param(base_workspace, "base_workspace", BaseWorkspaceRequestContext)

        branch_repo = _get_external_repo_from_context(
            branch_workspace, code_location_name, repository_name
        )
        if branch_repo is None:
            raise DagsterInvariantViolationError(
                f"Repository {repository_name} does not exist in code location {code_location_name} for the branch deployment."
            )
        base_repo = _get_external_repo_from_context(
            base_workspace, code_location_name, repository_name
        )
        return AssetGraphDiffer(
            branch_asset_graph=lambda: ExternalAssetGraph.from_external_repository(branch_repo),
            base_asset_graph=(lambda: ExternalAssetGraph.from_external_repository(base_repo))
            if base_repo is not None
            else None,
        )

    def _compare_base_and_branch_assets(self, asset_key: "AssetKey") -> Sequence[ChangeReason]:
        """Computes the diff between a branch deployment asset and the
        corresponding base deployment asset.
        """
        if self.base_asset_graph is None:
            # if the base asset graph is None, it is because the the asset graph in the branch deployment
            # is new and doesn't exist in the base deployment. Thus all assets are new.
            return [ChangeReason.NEW]

        if asset_key not in self.base_asset_graph.all_asset_keys:
            return [ChangeReason.NEW]

        changes = []
        if self.branch_asset_graph.get_code_version(
            asset_key
        ) != self.base_asset_graph.get_code_version(asset_key):
            changes.append(ChangeReason.CODE_VERSION)

        if self.branch_asset_graph.get_parents(asset_key) != self.base_asset_graph.get_parents(
            asset_key
        ):
            changes.append(ChangeReason.INPUTS)

        return changes

    def get_changes_for_asset(self, asset_key: "AssetKey") -> Sequence[ChangeReason]:
        """Returns list of ChangeReasons for asset_key as compared to the base deployment."""
        return self._compare_base_and_branch_assets(asset_key)

    @property
    def branch_asset_graph(self) -> "ExternalAssetGraph":
        if self._branch_asset_graph is None:
            self._branch_asset_graph = check.not_none(self._branch_asset_graph_load_fn)()
        return self._branch_asset_graph

    @property
    def base_asset_graph(self) -> Optional["ExternalAssetGraph"]:
        if self._base_asset_graph is None and self._base_asset_graph_load_fn is not None:
            self._base_asset_graph = self._base_asset_graph_load_fn()
        return self._base_asset_graph
