from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union

import dagster._check as check
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.remote_representation import ExternalRepository
from dagster._core.workspace.context import BaseWorkspaceRequestContext

if TYPE_CHECKING:
    from dagster._core.definitions.events import (
        AssetKey,
    )


class ChangeReason(Enum):
    NEW = "NEW"
    CODE_VERSION = "CODE_VERSION"
    INPUTS = "INPUTS"
    PARTITIONS_DEFINITION = "PARTITIONS_DEFINITION"


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

    _branch_asset_graph: Optional["RemoteAssetGraph"]
    _branch_asset_graph_load_fn: Optional[Callable[[], "RemoteAssetGraph"]]
    _base_asset_graph: Optional["RemoteAssetGraph"]
    _base_asset_graph_load_fn: Optional[Callable[[], "RemoteAssetGraph"]]

    def __init__(
        self,
        branch_asset_graph: Union["RemoteAssetGraph", Callable[[], "RemoteAssetGraph"]],
        base_asset_graph: Optional[
            Union["RemoteAssetGraph", Callable[[], "RemoteAssetGraph"]]
        ] = None,
    ):
        if base_asset_graph is None:
            # if base_asset_graph is None, then the asset graph in the branch deployment does not exist
            # in the base deployment
            self._base_asset_graph = None
            self._base_asset_graph_load_fn = None
        elif isinstance(base_asset_graph, RemoteAssetGraph):
            self._base_asset_graph = base_asset_graph
            self._base_asset_graph_load_fn = None
        else:
            self._base_asset_graph = None
            self._base_asset_graph_load_fn = base_asset_graph

        if isinstance(branch_asset_graph, RemoteAssetGraph):
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

        We cannot make RemoteAssetGraphs directly from the workspaces because if multiple code locations
        use the same asset key, those asset keys will override each other in the dictionaries the RemoteAssetGraph
        creates (see from_repository_handles_and_external_asset_nodes in RemoteAssetGraph). We need to ensure
        that we are comparing assets in the same code location and repository, so we need to make the
        RemoteAssetGraph from an ExternalRepository to ensure that there are no duplicate asset keys
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
            branch_asset_graph=lambda: branch_repo.asset_graph,
            base_asset_graph=(lambda: base_repo.asset_graph) if base_repo is not None else None,
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
        if (
            self.branch_asset_graph.get(asset_key).code_version
            != self.base_asset_graph.get(asset_key).code_version
        ):
            changes.append(ChangeReason.CODE_VERSION)

        if (
            self.branch_asset_graph.get(asset_key).parent_keys
            != self.base_asset_graph.get(asset_key).parent_keys
        ):
            changes.append(ChangeReason.INPUTS)
        else:
            # if the set of inputs is different, then we don't need to check if the partition mappings
            # for inputs have changed since ChangeReason.INPUTS is already in the list of changes
            for upstream_asset in self.branch_asset_graph.get(asset_key).parent_keys:
                if self.branch_asset_graph.get_partition_mapping(
                    asset_key, upstream_asset
                ) != self.base_asset_graph.get_partition_mapping(asset_key, upstream_asset):
                    changes.append(ChangeReason.INPUTS)
                    break

        if (
            self.branch_asset_graph.get(asset_key).partitions_def
            != self.base_asset_graph.get(asset_key).partitions_def
        ):
            changes.append(ChangeReason.PARTITIONS_DEFINITION)

        return changes

    def get_changes_for_asset(self, asset_key: "AssetKey") -> Sequence[ChangeReason]:
        """Returns list of ChangeReasons for asset_key as compared to the base deployment."""
        return self._compare_base_and_branch_assets(asset_key)

    @property
    def branch_asset_graph(self) -> "RemoteAssetGraph":
        if self._branch_asset_graph is None:
            self._branch_asset_graph = check.not_none(self._branch_asset_graph_load_fn)()
        return self._branch_asset_graph

    @property
    def base_asset_graph(self) -> Optional["RemoteAssetGraph"]:
        if self._base_asset_graph is None and self._base_asset_graph_load_fn is not None:
            self._base_asset_graph = self._base_asset_graph_load_fn()
        return self._base_asset_graph
