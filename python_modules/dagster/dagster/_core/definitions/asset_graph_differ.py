from enum import Enum
from typing import (
    AbstractSet,
    Any,
    Callable,
    Generic,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
)

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.remote_representation import RemoteRepository
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


class MappedKeyDiff(NamedTuple):
    added: AbstractSet[str]
    changed: AbstractSet[str]
    removed: AbstractSet[str]


T = TypeVar("T")


@whitelist_for_serdes
@record
class ValueDiff(Generic[T]):
    old: T
    new: T


@whitelist_for_serdes
@record
class DictDiff(Generic[T]):
    added_keys: AbstractSet[T]
    changed_keys: AbstractSet[T]
    removed_keys: AbstractSet[T]


@whitelist_for_serdes
@record
class AssetDefinitionDiffDetails:
    """Represents the diff information for changes between assets.

    Change types in change_types should have diff info for their corresponding fields
    if diff info is requested.

    "NEW" and "REMOVED" change types do not have diff info.
    """

    change_types: AbstractSet[AssetDefinitionChangeType]
    code_version: Optional[ValueDiff[Optional[str]]] = None
    dependencies: Optional[DictDiff[AssetKey]] = None
    partitions_definition: Optional[ValueDiff[Optional[str]]] = None
    tags: Optional[DictDiff[str]] = None
    metadata: Optional[DictDiff[str]] = None


def _get_remote_repo_from_context(
    context: BaseWorkspaceRequestContext, code_location_name: str, repository_name: str
) -> Optional[RemoteRepository]:
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
    def from_remote_repositories(
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
        creates (see from_repository_handles_and_asset_node_snaps in RemoteAssetGraph). We need to ensure
        that we are comparing assets in the same code location and repository, so we need to make the
        RemoteAssetGraph from an ExternalRepository to ensure that there are no duplicate asset keys
        that could override each other.
        """
        check.inst_param(branch_workspace, "branch_workspace", BaseWorkspaceRequestContext)
        check.inst_param(base_workspace, "base_workspace", BaseWorkspaceRequestContext)

        branch_repo = _get_remote_repo_from_context(
            branch_workspace, code_location_name, repository_name
        )
        if branch_repo is None:
            raise DagsterInvariantViolationError(
                f"Repository {repository_name} does not exist in code location {code_location_name} for the branch deployment."
            )
        base_repo = _get_remote_repo_from_context(
            base_workspace, code_location_name, repository_name
        )
        return AssetGraphDiffer(
            branch_asset_graph=lambda: branch_repo.asset_graph,
            base_asset_graph=(lambda: base_repo.asset_graph) if base_repo is not None else None,
        )

    def _compare_base_and_branch_assets(
        self, asset_key: "AssetKey", include_diff: bool = False
    ) -> AssetDefinitionDiffDetails:
        """Computes the diff between a branch deployment asset and the
        corresponding base deployment asset.
        """
        if self.base_asset_graph is None:
            # if the base asset graph is None, it is because the asset graph in the branch deployment
            # is new and doesn't exist in the base deployment. Thus all assets are new.
            return AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.NEW})

        if not self.base_asset_graph.has(asset_key):
            return AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.NEW})

        if not self.branch_asset_graph.has(asset_key):
            return AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.REMOVED})

        branch_asset = self.branch_asset_graph.get(asset_key)
        base_asset = self.base_asset_graph.get(asset_key)

        change_types: Set[AssetDefinitionChangeType] = set()
        code_version_diff: Optional[ValueDiff] = None
        dependencies_diff: Optional[DictDiff] = None
        partitions_definition_diff: Optional[ValueDiff] = None
        tags_diff: Optional[DictDiff] = None
        metadata_diff: Optional[DictDiff] = None

        if branch_asset.code_version != base_asset.code_version:
            change_types.add(AssetDefinitionChangeType.CODE_VERSION)
            if include_diff:
                code_version_diff = ValueDiff(
                    old=base_asset.code_version, new=branch_asset.code_version
                )

        if branch_asset.parent_keys != base_asset.parent_keys:
            change_types.add(AssetDefinitionChangeType.DEPENDENCIES)
            if include_diff:
                dependencies_diff = DictDiff(
                    added_keys=branch_asset.parent_keys - base_asset.parent_keys,
                    changed_keys=set(),
                    removed_keys=base_asset.parent_keys - branch_asset.parent_keys,
                )

        else:
            # if the set of upstream dependencies is different, then we don't need to check if the partition mappings
            # for dependencies have changed since ChangeReason.DEPENDENCIES is already in the list of changes
            for upstream_asset in branch_asset.parent_keys:
                if self.branch_asset_graph.get_partition_mapping(
                    asset_key, upstream_asset
                ) != self.base_asset_graph.get_partition_mapping(asset_key, upstream_asset):
                    change_types.add(AssetDefinitionChangeType.DEPENDENCIES)
                    if include_diff:
                        dependencies_diff = DictDiff(
                            added_keys=set(),
                            changed_keys={upstream_asset},
                            removed_keys=set(),
                        )
                    break

        if branch_asset.partitions_def != base_asset.partitions_def:
            change_types.add(AssetDefinitionChangeType.PARTITIONS_DEFINITION)
            if include_diff:
                partitions_definition_diff = ValueDiff(
                    old=type(base_asset.partitions_def).__name__
                    if base_asset.partitions_def
                    else None,
                    new=type(branch_asset.partitions_def).__name__
                    if branch_asset.partitions_def
                    else None,
                )

        if branch_asset.tags != base_asset.tags:
            change_types.add(AssetDefinitionChangeType.TAGS)
            if include_diff:
                added, changed, removed = self._get_map_keys_diff(
                    base_asset.tags, branch_asset.tags
                )
                tags_diff = DictDiff(added_keys=added, changed_keys=changed, removed_keys=removed)

        if branch_asset.metadata != base_asset.metadata:
            change_types.add(AssetDefinitionChangeType.METADATA)
            if include_diff:
                added, changed, removed = self._get_map_keys_diff(
                    base_asset.metadata, branch_asset.metadata
                )
                metadata_diff = DictDiff(
                    added_keys=added, changed_keys=changed, removed_keys=removed
                )

        return AssetDefinitionDiffDetails(
            change_types=change_types,
            code_version=code_version_diff,
            dependencies=dependencies_diff,
            partitions_definition=partitions_definition_diff,
            tags=tags_diff,
            metadata=metadata_diff,
        )

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
        return list(self._compare_base_and_branch_assets(asset_key).change_types)

    def get_changes_for_asset_with_diff(self, asset_key: "AssetKey") -> AssetDefinitionDiffDetails:
        """Returns list of AssetDefinitionDiff for asset_key as compared to the base deployment."""
        return self._compare_base_and_branch_assets(asset_key, include_diff=True)

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
