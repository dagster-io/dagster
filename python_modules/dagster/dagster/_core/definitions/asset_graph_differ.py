from collections.abc import Mapping, Sequence, Set
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, NamedTuple, Optional, TypeVar

from dagster._core.definitions.events import AssetKey
from dagster._record import record
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph


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
    added: Set[str]
    changed: Set[str]
    removed: Set[str]


T = TypeVar("T")


@whitelist_for_serdes
@record
class ValueDiff(Generic[T]):
    old: T
    new: T


@whitelist_for_serdes
@record
class DictDiff(Generic[T]):
    added_keys: Set[T]
    changed_keys: Set[T]
    removed_keys: Set[T]


@whitelist_for_serdes
@record
class AssetDefinitionDiffDetails:
    """Represents the diff information for changes between assets.

    Change types in change_types should have diff info for their corresponding fields
    if diff info is requested.

    "NEW" and "REMOVED" change types do not have diff info.
    """

    change_types: Set[AssetDefinitionChangeType]
    code_version: Optional[ValueDiff[Optional[str]]] = None
    dependencies: Optional[DictDiff[AssetKey]] = None
    partitions_definition: Optional[ValueDiff[Optional[str]]] = None
    tags: Optional[DictDiff[str]] = None
    metadata: Optional[DictDiff[str]] = None


class AssetGraphDiffer:
    """Given two asset graphs, base_asset_graph and branch_asset_graph, we can compute how the
    assets in branch_asset_graph have changed with respect to base_asset_graph. The ChangeReason
    enum contains the list of potential changes an asset can undergo. If the base_asset_graph is None,
    this indicates that the branch_asset_graph does not yet exist in the base deployment. In this case
    we will consider every asset New.
    """

    def __init__(
        self,
        branch_asset_graph: "RemoteAssetGraph",
        base_asset_graph: "RemoteAssetGraph",
    ):
        self._branch_asset_graph = branch_asset_graph
        self._base_asset_graph = base_asset_graph

    def _compare_base_and_branch_assets(
        self, asset_key: "AssetKey", include_diff: bool = False
    ) -> AssetDefinitionDiffDetails:
        """Computes the diff between a branch deployment asset and the
        corresponding base deployment asset.
        """
        if not self._base_asset_graph.has(asset_key):
            # if the base asset graph is None, it is because the asset graph in the branch deployment
            # is new and doesn't exist in the base deployment. Thus all assets are new.
            return AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.NEW})

        if not self._branch_asset_graph.has(asset_key):
            return AssetDefinitionDiffDetails(change_types={AssetDefinitionChangeType.REMOVED})

        base_asset = self._base_asset_graph.get(asset_key).resolve_to_singular_repo_scoped_node()

        # This may not detect the case where an asset is moved from one repository or code location
        # to another as a change.
        branch_asset = self._branch_asset_graph.get(
            asset_key
        ).resolve_to_singular_repo_scoped_node()

        change_types: set[AssetDefinitionChangeType] = set()
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
            for upstream_asset_key in branch_asset.parent_keys:
                if branch_asset.partition_mappings.get(
                    upstream_asset_key
                ) != base_asset.partition_mappings.get(upstream_asset_key):
                    change_types.add(AssetDefinitionChangeType.DEPENDENCIES)
                    if include_diff:
                        dependencies_diff = DictDiff(
                            added_keys=set(),
                            changed_keys={upstream_asset_key},
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
