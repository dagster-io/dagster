import itertools
import warnings
from collections import defaultdict
from enum import Enum
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.base_asset_graph import (
    AssetCheckNode,
    AssetKey,
    BaseAssetGraph,
    BaseAssetNode,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.workspace.workspace import WorkspaceSnapshot

if TYPE_CHECKING:
    from dagster._core.remote_representation.external_data import AssetCheckNodeSnap, AssetNodeSnap
    from dagster._core.selector.subset_selector import DependencyGraph


class RemoteAssetNode(BaseAssetNode):
    def __init__(
        self,
        key: AssetKey,
        parent_keys: AbstractSet[AssetKey],
        child_keys: AbstractSet[AssetKey],
        execution_set_keys: AbstractSet[EntityKey],
        repo_node_pairs: Sequence[Tuple[RepositoryHandle, "AssetNodeSnap"]],
        check_keys: AbstractSet[AssetCheckKey],
    ):
        self.key = key
        self.parent_keys = parent_keys
        self.child_keys = child_keys
        self._repo_node_pairs = repo_node_pairs
        self._asset_node_snaps = [node for _, node in repo_node_pairs]
        self._check_keys = check_keys
        self._execution_set_keys = execution_set_keys

    ##### COMMON ASSET NODE INTERFACE

    @property
    def description(self) -> Optional[str]:
        return self.priority_node_snap.description

    @property
    def group_name(self) -> str:
        return self.priority_node_snap.group_name or DEFAULT_GROUP_NAME

    @cached_property
    def is_materializable(self) -> bool:
        return any(node.is_materializable for node in self._asset_node_snaps)

    @cached_property
    def is_observable(self) -> bool:
        return any(node.is_observable for node in self._asset_node_snaps)

    @cached_property
    def is_external(self) -> bool:
        return all(node.is_external for node in self._asset_node_snaps)

    @cached_property
    def is_executable(self) -> bool:
        return any(node.is_executable for node in self._asset_node_snaps)

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self.priority_node_snap.metadata

    @property
    def tags(self) -> Mapping[str, str]:
        return self.priority_node_snap.tags or {}

    @property
    def owners(self) -> Sequence[str]:
        return self.priority_node_snap.owners or []

    @property
    def is_partitioned(self) -> bool:
        return self.priority_node_snap.partitions is not None

    @cached_property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        partitions_snap = self.priority_node_snap.partitions
        return partitions_snap.get_partitions_definition() if partitions_snap else None

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        if self.is_materializable:
            return {
                dep.parent_asset_key: dep.partition_mapping
                for dep in self._materializable_node_snap.parent_edges
                if dep.partition_mapping is not None
            }
        else:
            return {}

    @property
    def freshness_policy(self) -> Optional[FreshnessPolicy]:
        # It is currently not possible to access the freshness policy for an observation definition
        # if a materialization definition also exists. This needs to be fixed.
        return self.priority_node_snap.freshness_policy

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return (
            self._materializable_node_snap.auto_materialize_policy
            if self.is_materializable
            else None
        )

    @property
    def automation_condition(self) -> Optional[AutomationCondition]:
        if self.is_materializable:
            return self._materializable_node_snap.automation_condition
        elif self.is_observable:
            return self._observable_node_snap.automation_condition
        else:
            return None

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return (
            self._observable_node_snap.auto_observe_interval_minutes if self.is_observable else None
        )

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self._materializable_node_snap.backfill_policy if self.is_materializable else None

    @property
    def code_version(self) -> Optional[str]:
        # It is currently not possible to access the code version for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self.priority_node_snap.code_version

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self._check_keys

    @property
    def execution_set_asset_keys(self) -> AbstractSet[AssetKey]:
        return {k for k in self.execution_set_entity_keys if isinstance(k, AssetKey)}

    @property
    def execution_set_entity_keys(self) -> AbstractSet[EntityKey]:
        return self._execution_set_keys

    ##### REMOTE-SPECIFIC INTERFACE

    @property
    def job_names(self) -> Sequence[str]:
        # It is currently not possible to access the job names for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self.priority_node_snap.job_names if self.is_executable else []

    @property
    def priority_repository_handle(self) -> RepositoryHandle:
        # This property supports existing behavior but it should be phased out, because it relies on
        # materialization nodes shadowing observation nodes that would otherwise be exposed.
        return next(
            itertools.chain(
                (repo for repo, node in self._repo_node_pairs if node.is_materializable),
                (repo for repo, node in self._repo_node_pairs if node.is_observable),
                (repo for repo, node in self._repo_node_pairs),
            )
        )

    @property
    def repository_handles(self) -> Sequence[RepositoryHandle]:
        return [repo_handle for repo_handle, _ in self._repo_node_pairs]

    @property
    def repo_node_pairs(self) -> Sequence[Tuple[RepositoryHandle, "AssetNodeSnap"]]:
        return self._repo_node_pairs

    @cached_property
    def priority_node_snap(self) -> "AssetNodeSnap":
        # Return a materialization node if it exists, otherwise return an observable node if it
        # exists, otherwise return any node. This exists to preserve implicit behavior, where the
        # materialization node was previously preferred over the observable node. This is a
        # temporary measure until we can appropriately scope the accessors that could apply to
        # either a materialization or observation node.
        return next(
            itertools.chain(
                (node for node in self._asset_node_snaps if node.is_materializable),
                (node for node in self._asset_node_snaps if node.is_observable),
                (node for node in self._asset_node_snaps),
            )
        )

    ##### HELPERS

    @cached_property
    def _materializable_node_snap(self) -> "AssetNodeSnap":
        try:
            return next(node for node in self._asset_node_snaps if node.is_materializable)
        except StopIteration:
            check.failed("No materializable node found")

    @cached_property
    def _observable_node_snap(self) -> "AssetNodeSnap":
        try:
            return next((node for node in self._asset_node_snaps if node.is_observable))
        except StopIteration:
            check.failed("No observable node found")


class RemoteAssetGraphScope(Enum):
    """Was this asset graph built from a single repository or all repositories across the whole workspace."""

    REPOSITORY = "REPOSITORY"
    WORKSPACE = "WORKSPACE"


class RemoteAssetGraph(BaseAssetGraph[RemoteAssetNode]):
    def __init__(
        self,
        scope: RemoteAssetGraphScope,
        asset_nodes_by_key: Mapping[AssetKey, RemoteAssetNode],
        asset_checks_by_key: Mapping[AssetCheckKey, "AssetCheckNodeSnap"],
        asset_check_execution_sets_by_key: Mapping[AssetCheckKey, AbstractSet[EntityKey]],
        repository_handles_by_asset_check_key: Mapping[AssetCheckKey, RepositoryHandle],
    ):
        self._scope = scope
        self._asset_nodes_by_key = asset_nodes_by_key
        self._asset_checks_by_key = asset_checks_by_key
        self._asset_check_nodes_by_key = {
            k: AssetCheckNode(k, v.blocking, v.automation_condition)
            for k, v in asset_checks_by_key.items()
        }
        self._asset_check_execution_sets_by_key = asset_check_execution_sets_by_key
        self._repository_handles_by_asset_check_key = repository_handles_by_asset_check_key

    @classmethod
    def from_remote_repository(cls, repo: RemoteRepository):
        return cls._build(
            scope=RemoteAssetGraphScope.REPOSITORY,
            repo_handle_assets=[
                (repo.handle, node_snap) for node_snap in repo.get_asset_node_snaps()
            ],
            repo_handle_asset_checks=[
                (repo.handle, asset_check_node)
                for asset_check_node in repo.get_asset_check_node_snaps()
            ],
        )

    @classmethod
    def from_workspace_snapshot(cls, workspace: WorkspaceSnapshot):
        code_locations = (
            location_entry.code_location
            for location_entry in workspace.code_location_entries.values()
            if location_entry.code_location
        )
        repos = (
            repo
            for code_location in code_locations
            for repo in code_location.get_repositories().values()
        )

        repo_handle_assets: Sequence[Tuple["RepositoryHandle", "AssetNodeSnap"]] = []
        repo_handle_asset_checks: Sequence[Tuple["RepositoryHandle", "AssetCheckNodeSnap"]] = []
        for repo in repos:
            for asset_node_snap in repo.get_asset_node_snaps():
                repo_handle_assets.append((repo.handle, asset_node_snap))
            for asset_check_node_snap in repo.get_asset_check_node_snaps():
                repo_handle_asset_checks.append((repo.handle, asset_check_node_snap))

        return cls._build(
            scope=RemoteAssetGraphScope.WORKSPACE,
            repo_handle_assets=repo_handle_assets,
            repo_handle_asset_checks=repo_handle_asset_checks,
        )

    @classmethod
    def _build(
        cls,
        scope: RemoteAssetGraphScope,
        repo_handle_assets: Sequence[Tuple[RepositoryHandle, "AssetNodeSnap"]],
        repo_handle_asset_checks: Sequence[Tuple[RepositoryHandle, "AssetCheckNodeSnap"]],
    ) -> "RemoteAssetGraph":
        _warn_on_duplicate_nodes(repo_handle_assets)

        # Build an index of execution sets by key. An execution set is a set of assets and checks
        # that must be executed together. AssetNodeSnaps and AssetCheckNodeSnaps already have an
        # optional execution_set_identifier set. A null execution_set_identifier indicates that the
        # node or check can be executed independently.
        assets = [asset for _, asset in repo_handle_assets]
        asset_checks = [asset_check for _, asset_check in repo_handle_asset_checks]
        execution_sets_by_key = _build_execution_set_index(assets, asset_checks)

        # Index all (RepositoryHandle, AssetNodeSnap) pairs by their asset key, then use this to
        # build the set of RemoteAssetNodes (indexed by key). Each RemoteAssetNode wraps the set of
        # pairs for an asset key.
        repo_node_pairs_by_key: Dict[AssetKey, List[Tuple[RepositoryHandle, "AssetNodeSnap"]]] = (
            defaultdict(list)
        )

        # Build the dependency graph of asset keys.
        all_keys = {asset.asset_key for asset in assets}
        upstream: Dict[AssetKey, Set[AssetKey]] = {key: set() for key in all_keys}
        downstream: Dict[AssetKey, Set[AssetKey]] = {key: set() for key in all_keys}

        for repo_handle, node in repo_handle_assets:
            repo_node_pairs_by_key[node.asset_key].append((repo_handle, node))
            for dep in node.parent_edges:
                upstream[node.asset_key].add(dep.parent_asset_key)
                downstream[dep.parent_asset_key].add(node.asset_key)

        dep_graph: DependencyGraph[AssetKey] = {"upstream": upstream, "downstream": downstream}

        # Build the set of ExternalAssetChecks, indexed by key. Also the index of execution units for
        # each asset check key.
        check_keys_by_asset_key: Dict[AssetKey, Set[AssetCheckKey]] = defaultdict(set)
        asset_checks_by_key: Dict[AssetCheckKey, "AssetCheckNodeSnap"] = {}
        repository_handles_by_asset_check_key: Dict[AssetCheckKey, RepositoryHandle] = {}
        for repo_handle, asset_check in repo_handle_asset_checks:
            asset_checks_by_key[asset_check.key] = asset_check
            check_keys_by_asset_key[asset_check.asset_key].add(asset_check.key)
            repository_handles_by_asset_check_key[asset_check.key] = repo_handle

        asset_check_execution_sets_by_key = {
            k: v for k, v in execution_sets_by_key.items() if isinstance(k, AssetCheckKey)
        }
        # Build the set of RemoteAssetNodes in topological order so that each node can hold
        # references to its parents.
        asset_nodes_by_key = {
            key: RemoteAssetNode(
                key=key,
                parent_keys=dep_graph["upstream"][key],
                child_keys=dep_graph["downstream"][key],
                execution_set_keys=execution_sets_by_key[key],
                repo_node_pairs=repo_node_pairs,
                check_keys=check_keys_by_asset_key[key],
            )
            for key, repo_node_pairs in repo_node_pairs_by_key.items()
        }

        return cls(
            scope,
            asset_nodes_by_key,
            asset_checks_by_key,
            asset_check_execution_sets_by_key,
            repository_handles_by_asset_check_key,
        )

    ##### COMMON ASSET GRAPH INTERFACE

    def get_execution_set_asset_and_check_keys(
        self, entity_key: EntityKey
    ) -> AbstractSet[EntityKey]:
        if isinstance(entity_key, AssetKey):
            return self.get(entity_key).execution_set_entity_keys
        else:  # AssetCheckKey
            return self._asset_check_execution_sets_by_key[entity_key]

    ##### REMOTE-SPECIFIC METHODS

    @property
    def asset_node_snaps_by_key(self) -> Mapping[AssetKey, "AssetNodeSnap"]:
        # This exists to support existing callsites but it should be removed ASAP, since it exposes
        # `AssetNodeSnap` instances directly. All sites using this should use RemoteAssetNode
        # instead.
        return {k: node.priority_node_snap for k, node in self._asset_nodes_by_key.items()}

    @property
    def asset_checks(self) -> Sequence["AssetCheckNodeSnap"]:
        return list(self._asset_checks_by_key.values())

    @cached_property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return set(self._asset_checks_by_key.keys())

    def asset_keys_for_job(self, job_name: str) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if job_name in node.job_names}

    @cached_property
    def all_job_names(self) -> AbstractSet[str]:
        return {job_name for node in self.asset_nodes for job_name in node.job_names}

    @cached_property
    def repository_handles_by_key(self) -> Mapping[EntityKey, RepositoryHandle]:
        return {
            **{k: node.priority_repository_handle for k, node in self._asset_nodes_by_key.items()},
            **self._repository_handles_by_asset_check_key,
        }

    def get_repository_handle(self, key: EntityKey) -> RepositoryHandle:
        return self.repository_handles_by_key[key]

    def get_materialization_job_names(self, asset_key: AssetKey) -> Sequence[str]:
        """Returns the names of jobs that materialize this asset."""
        # This is a poorly named method because it will expose observation job names for assets with
        # a defined observation but no materialization.
        return self.get(asset_key).job_names

    def get_materialization_asset_keys_for_job(self, job_name: str) -> Sequence[AssetKey]:
        """Returns asset keys that are targeted for materialization in the given job."""
        return [
            k
            for k in self.materializable_asset_keys
            if job_name in self.get_materialization_job_names(k)
        ]

    def get_implicit_job_name_for_assets(
        self,
        asset_keys: Iterable[AssetKey],
        external_repo: Optional[RemoteRepository],
    ) -> Optional[str]:
        """Returns the name of the asset base job that contains all the given assets, or None if there is no such
        job.

        Note: all asset_keys should be in the same repository.
        """
        return IMPLICIT_ASSET_JOB_NAME

    def split_entity_keys_by_repository(
        self, keys: AbstractSet[EntityKey]
    ) -> Sequence[AbstractSet[EntityKey]]:
        keys_by_repo = defaultdict(set)
        for key in keys:
            repo_handle = self.get_repository_handle(key)
            keys_by_repo[(repo_handle.location_name, repo_handle.repository_name)].add(key)
        return list(keys_by_repo.values())


def _warn_on_duplicate_nodes(
    repo_handle_asset_node_snaps: Sequence[Tuple[RepositoryHandle, "AssetNodeSnap"]],
) -> None:
    # Split the nodes into materializable, observable, and unexecutable nodes. Observable and
    # unexecutable `AssetNodeSnap` represent both source and external assets-- the
    # "External" in "AssetNodeSnap" is unrelated to the "external" in "external asset", this
    # is just an unfortunate naming collision. `AssetNodeSnap` will be renamed eventually.
    materializable_node_pairs: List[Tuple[RepositoryHandle, "AssetNodeSnap"]] = []
    observable_node_pairs: List[Tuple[RepositoryHandle, "AssetNodeSnap"]] = []
    unexecutable_node_pairs: List[Tuple[RepositoryHandle, "AssetNodeSnap"]] = []
    for repo_handle, node in repo_handle_asset_node_snaps:
        if node.is_source and node.is_observable:
            observable_node_pairs.append((repo_handle, node))
        elif node.is_source:
            unexecutable_node_pairs.append((repo_handle, node))
        else:
            materializable_node_pairs.append((repo_handle, node))

    # It is possible for multiple nodes to exist that share the same key. This is invalid if
    # more than one node is materializable or if more than one node is observable. It is valid
    # if there is at most one materializable node and at most one observable node, with all
    # other nodes unexecutable.
    _warn_on_duplicates_within_subset(materializable_node_pairs, AssetExecutionType.MATERIALIZATION)
    _warn_on_duplicates_within_subset(observable_node_pairs, AssetExecutionType.OBSERVATION)


def _warn_on_duplicates_within_subset(
    node_pairs: Sequence[Tuple[RepositoryHandle, "AssetNodeSnap"]],
    execution_type: AssetExecutionType,
) -> None:
    repo_handles_by_asset_key: DefaultDict[AssetKey, List[RepositoryHandle]] = defaultdict(list)
    for repo_handle, node in node_pairs:
        repo_handles_by_asset_key[node.asset_key].append(repo_handle)

    duplicates = {k: v for k, v in repo_handles_by_asset_key.items() if len(v) > 1}
    duplicate_lines = []
    for asset_key, repo_handles in duplicates.items():
        locations = [repo_handle.code_location_origin.location_name for repo_handle in repo_handles]
        duplicate_lines.append(f"  {asset_key.to_string()}: {locations}")
    duplicate_str = "\n".join(duplicate_lines)
    if duplicates:
        warnings.warn(
            f"Found {execution_type.value} nodes for some asset keys in multiple code locations."
            f" Only one {execution_type.value} node is allowed per asset key. Duplicates:\n {duplicate_str}"
        )


def _build_execution_set_index(
    asset_node_snaps: Iterable["AssetNodeSnap"],
    asset_check_node_snaps: Iterable["AssetCheckNodeSnap"],
) -> Mapping[EntityKey, AbstractSet[EntityKey]]:
    from dagster._core.remote_representation.external_data import AssetNodeSnap

    all_items = [*asset_node_snaps, *asset_check_node_snaps]

    execution_sets_by_id: Dict[str, Set[EntityKey]] = defaultdict(set)
    for item in all_items:
        id = item.execution_set_identifier
        key = item.asset_key if isinstance(item, AssetNodeSnap) else item.key
        if id is not None:
            execution_sets_by_id[id].add(key)

    execution_sets_by_key: Dict[EntityKey, Set[EntityKey]] = {}
    for item in all_items:
        id = item.execution_set_identifier
        key = item.asset_key if isinstance(item, AssetNodeSnap) else item.key
        execution_sets_by_key[key] = execution_sets_by_id[id] if id is not None else {key}

    return execution_sets_by_key
