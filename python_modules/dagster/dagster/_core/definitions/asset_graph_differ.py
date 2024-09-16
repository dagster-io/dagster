from enum import Enum
from typing import AbstractSet, Any, Callable, Mapping, NamedTuple, Optional, Sequence, Set, Union

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.remote_representation import ExternalRepository
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._record import record
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetDefinitionChangeType(Enum):
    """What change an asset has undergone between two deployments. Used
    in distinguishing asset definition changes in branch deployment and
    in subsequent other deployments.
    """

    NEW = "NEW"
    CODE_VERSION = "CODE_VERSION"
    DEPENDENCIES = "DEPENDENCIES"
    PARTITIONS_DEFINITION = "PARTITIONS_DEFINITION"
    TAGS = "TAGS"
    METADATA = "METADATA"
    REMOVED = "REMOVED"


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailNew:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.NEW


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailCodeVersion:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.CODE_VERSION
    base_value: Optional[str] = None
    branch_value: Optional[str] = None


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailDependencies:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.DEPENDENCIES
    added: AbstractSet[AssetKey] = set()
    changed: AbstractSet[AssetKey] = set()
    removed: AbstractSet[AssetKey] = set()


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailPartitionsDefinition:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.PARTITIONS_DEFINITION
    base_value: Optional[str] = None
    branch_value: Optional[str] = None


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailTags:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.TAGS
    added: Sequence[str] = []
    changed: Sequence[str] = []
    removed: Sequence[str] = []


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailMetadata:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.METADATA
    added: Sequence[str] = []
    changed: Sequence[str] = []
    removed: Sequence[str] = []


@whitelist_for_serdes
@record
class AssetDefinitionChangeDetailRemoved:
    change_type: AssetDefinitionChangeType = AssetDefinitionChangeType.REMOVED


"""Represents the diff information for changes between base and branch assets."""
AssetDefinitionChangeDetail = Union[
    AssetDefinitionChangeDetailNew,
    AssetDefinitionChangeDetailCodeVersion,
    AssetDefinitionChangeDetailDependencies,
    AssetDefinitionChangeDetailPartitionsDefinition,
    AssetDefinitionChangeDetailTags,
    AssetDefinitionChangeDetailMetadata,
    AssetDefinitionChangeDetailRemoved,
]


class MappedKeyDiff(NamedTuple):
    added: Set[str]
    changed: Set[str]
    removed: Set[str]


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

    def _compare_base_and_branch_assets(
        self, asset_key: "AssetKey", include_details: bool = False
    ) -> Sequence[AssetDefinitionChangeDetail]:
        """Computes the diff between a branch deployment asset and the
        corresponding base deployment asset.
        """
        if self.base_asset_graph is None:
            # if the base asset graph is None, it is because the asset graph in the branch deployment
            # is new and doesn't exist in the base deployment. Thus all assets are new.
            return [AssetDefinitionChangeDetailNew()]

        if asset_key not in self.base_asset_graph.all_asset_keys:
            return [AssetDefinitionChangeDetailNew()]

        if asset_key not in self.branch_asset_graph.all_asset_keys:
            return [AssetDefinitionChangeDetailRemoved()]

        branch_asset = self.branch_asset_graph.get(asset_key)
        base_asset = self.base_asset_graph.get(asset_key)

        changes: Sequence[AssetDefinitionChangeDetail] = []
        if branch_asset.code_version != base_asset.code_version:
            if include_details:
                changes.append(
                    AssetDefinitionChangeDetailCodeVersion(
                        base_value=base_asset.code_version, branch_value=branch_asset.code_version
                    )
                )
            else:
                changes.append(AssetDefinitionChangeDetailCodeVersion())

        if branch_asset.parent_keys != base_asset.parent_keys:
            if include_details:
                changes.append(
                    AssetDefinitionChangeDetailDependencies(
                        added=branch_asset.parent_keys - base_asset.parent_keys,
                        removed=base_asset.parent_keys - branch_asset.parent_keys,
                    )
                )
            else:
                changes.append(AssetDefinitionChangeDetailDependencies())
        else:
            # if the set of upstream dependencies is different, then we don't need to check if the partition mappings
            # for dependencies have changed since ChangeReason.DEPENDENCIES is already in the list of changes
            for upstream_asset in branch_asset.parent_keys:
                if self.branch_asset_graph.get_partition_mapping(
                    asset_key, upstream_asset
                ) != self.base_asset_graph.get_partition_mapping(asset_key, upstream_asset):
                    if include_details:
                        changes.append(
                            AssetDefinitionChangeDetailDependencies(changed={upstream_asset})
                        )
                    else:
                        changes.append(AssetDefinitionChangeDetailDependencies())
                    break

        if branch_asset.partitions_def != base_asset.partitions_def:
            if include_details:
                changes.append(
                    AssetDefinitionChangeDetailPartitionsDefinition(
                        base_value=type(base_asset.partitions_def).__name__
                        if base_asset.partitions_def
                        else None,
                        branch_value=type(branch_asset.partitions_def).__name__
                        if branch_asset.partitions_def
                        else None,
                    )
                )
            else:
                changes.append(AssetDefinitionChangeDetailPartitionsDefinition())

        if branch_asset.tags != base_asset.tags:
            if include_details:
                added, changed, removed = self._get_map_keys_diff(
                    base_asset.tags, branch_asset.tags
                )
                changes.append(
                    AssetDefinitionChangeDetailTags(
                        added=list(added), changed=list(changed), removed=list(removed)
                    )
                )
            else:
                changes.append(AssetDefinitionChangeDetailTags())

        if branch_asset.metadata != base_asset.metadata:
            if include_details:
                added, changed, removed = self._get_map_keys_diff(
                    base_asset.metadata, branch_asset.metadata
                )
                changes.append(
                    AssetDefinitionChangeDetailMetadata(
                        added=list(added), changed=list(changed), removed=list(removed)
                    )
                )
            else:
                changes.append(AssetDefinitionChangeDetailMetadata())

        return changes

    def _get_map_keys_diff(
        self, base: Mapping[str, Any], branch: Mapping[str, Any]
    ) -> MappedKeyDiff:
        """Returns the added, changed, and removed keys in the branch map compared to the base map."""
        added = set(branch.keys()) - set(base.keys())
        changed = {key for key in branch.keys() if key in base and branch[key] != base[key]}
        removed = set(base.keys()) - set(branch.keys())
        return MappedKeyDiff(added, changed, removed)

    def get_changes_for_asset(self, asset_key: "AssetKey") -> Sequence[AssetDefinitionChangeType]:
        """Returns list of AssetDefinitionChangeType for asset_key as compared to the base deployment."""
        return [change.change_type for change in self._compare_base_and_branch_assets(asset_key)]

    def get_changes_for_asset_with_details(
        self, asset_key: "AssetKey"
    ) -> Sequence[AssetDefinitionChangeDetail]:
        """Returns list of AssetDefinitionChangeDetail for asset_key as compared to the base deployment."""
        return self._compare_base_and_branch_assets(asset_key, include_details=True)

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
