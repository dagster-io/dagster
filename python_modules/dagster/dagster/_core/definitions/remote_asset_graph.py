import itertools
import warnings
from collections import defaultdict
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
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.base_asset_graph import (
    AssetKeyOrCheckKey,
    BaseAssetGraph,
    BaseAssetNode,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.remote_representation.external import ExternalRepository
from dagster._core.remote_representation.handle import RepositoryHandle

if TYPE_CHECKING:
    from dagster._core.remote_representation.external_data import (
        ExternalAssetCheck,
        ExternalAssetNode,
    )
    from dagster._core.selector.subset_selector import DependencyGraph


class RemoteAssetNode(BaseAssetNode):
    def __init__(
        self,
        key: AssetKey,
        parent_keys: AbstractSet[AssetKey],
        child_keys: AbstractSet[AssetKey],
        execution_set_keys: AbstractSet[AssetKeyOrCheckKey],
        repo_node_pairs: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
        check_keys: AbstractSet[AssetCheckKey],
    ):
        self.key = key
        self.parent_keys = parent_keys
        self.child_keys = child_keys
        self._repo_node_pairs = repo_node_pairs
        self._external_asset_nodes = [node for _, node in repo_node_pairs]
        self._check_keys = check_keys
        self._execution_set_keys = execution_set_keys

    ##### COMMON ASSET NODE INTERFACE

    @property
    def description(self) -> Optional[str]:
        return self._priority_node.description

    @property
    def group_name(self) -> str:
        return self._priority_node.group_name or DEFAULT_GROUP_NAME

    @cached_property
    def is_materializable(self) -> bool:
        return any(node.is_materializable for node in self._external_asset_nodes)

    @cached_property
    def is_observable(self) -> bool:
        return any(node.is_observable for node in self._external_asset_nodes)

    @cached_property
    def is_external(self) -> bool:
        return all(node.is_external for node in self._external_asset_nodes)

    @cached_property
    def is_executable(self) -> bool:
        return any(node.is_executable for node in self._external_asset_nodes)

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self._priority_node.metadata

    @property
    def tags(self) -> Mapping[str, str]:
        return self._priority_node.tags or {}

    @property
    def owners(self) -> Sequence[str]:
        return self._priority_node.owners or []

    @property
    def is_partitioned(self) -> bool:
        return self._priority_node.partitions_def_data is not None

    @cached_property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        external_def = self._priority_node.partitions_def_data
        return external_def.get_partitions_definition() if external_def else None

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        if self.is_materializable:
            return {
                dep.upstream_asset_key: dep.partition_mapping
                for dep in self._materializable_node.dependencies
                if dep.partition_mapping is not None
            }
        else:
            return {}

    @property
    def freshness_policy(self) -> Optional[FreshnessPolicy]:
        # It is currently not possible to access the freshness policy for an observation definition
        # if a materialization definition also exists. This needs to be fixed.
        return self._priority_node.freshness_policy

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self._materializable_node.auto_materialize_policy if self.is_materializable else None

    @property
    def automation_condition(self) -> Optional[AutomationCondition]:
        if self.is_materializable:
            return self._materializable_node.automation_condition
        elif self.is_observable:
            return self._observable_node.automation_condition
        else:
            return None

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return self._observable_node.auto_observe_interval_minutes if self.is_observable else None

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self._materializable_node.backfill_policy if self.is_materializable else None

    @property
    def code_version(self) -> Optional[str]:
        # It is currently not possible to access the code version for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self._priority_node.code_version

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self._check_keys

    @property
    def execution_set_asset_keys(self) -> AbstractSet[AssetKey]:
        return {k for k in self.execution_set_asset_and_check_keys if isinstance(k, AssetKey)}

    @property
    def execution_set_asset_and_check_keys(self) -> AbstractSet[AssetKeyOrCheckKey]:
        return self._execution_set_keys

    ##### REMOTE-SPECIFIC INTERFACE

    @property
    def job_names(self) -> Sequence[str]:
        # It is currently not possible to access the job names for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self._priority_node.job_names if self.is_executable else []

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

    ##### HELPERS

    @cached_property
    def _priority_node(self) -> "ExternalAssetNode":
        # Return a materialization node if it exists, otherwise return an observable node if it
        # exists, otherwise return any node. This exists to preserve implicit behavior, where the
        # materialization node was previously preferred over the observable node. This is a
        # temporary measure until we can appropriately scope the accessors that could apply to
        # either a materialization or observation node.
        return next(
            itertools.chain(
                (node for node in self._external_asset_nodes if node.is_materializable),
                (node for node in self._external_asset_nodes if node.is_observable),
                (node for node in self._external_asset_nodes),
            )
        )

    @cached_property
    def _materializable_node(self) -> "ExternalAssetNode":
        try:
            return next(node for node in self._external_asset_nodes if node.is_materializable)
        except StopIteration:
            check.failed("No materializable node found")

    @cached_property
    def _observable_node(self) -> "ExternalAssetNode":
        try:
            return next((node for node in self._external_asset_nodes if node.is_observable))
        except StopIteration:
            check.failed("No observable node found")


class RemoteAssetGraph(BaseAssetGraph[RemoteAssetNode]):
    def __init__(
        self,
        asset_nodes_by_key: Mapping[AssetKey, RemoteAssetNode],
        asset_checks_by_key: Mapping[AssetCheckKey, "ExternalAssetCheck"],
        asset_check_execution_sets_by_key: Mapping[AssetCheckKey, AbstractSet[AssetKeyOrCheckKey]],
    ):
        self._asset_nodes_by_key = asset_nodes_by_key
        self._asset_checks_by_key = asset_checks_by_key
        self._asset_check_execution_sets_by_key = asset_check_execution_sets_by_key

    @classmethod
    def from_repository_handles_and_external_asset_nodes(
        cls,
        repo_handle_external_asset_nodes: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
        external_asset_checks: Sequence["ExternalAssetCheck"],
    ) -> "RemoteAssetGraph":
        _warn_on_duplicate_nodes(repo_handle_external_asset_nodes)

        # Build an index of execution sets by key. An execution set is a set of assets and checks
        # that must be executed together. ExternalAssetNodes and ExternalAssetChecks already have an
        # optional execution_set_identifier set. A null execution_set_identifier indicates that the
        # node or check can be executed independently.
        execution_sets_by_key = _build_execution_set_index(
            (node for _, node in repo_handle_external_asset_nodes),
            external_asset_checks,
        )

        # Index all (RepositoryHandle, ExternalAssetNode) pairs by their asset key, then use this to
        # build the set of RemoteAssetNodes (indexed by key). Each RemoteAssetNode wraps the set of
        # pairs for an asset key.
        repo_node_pairs_by_key: Dict[
            AssetKey, List[Tuple[RepositoryHandle, "ExternalAssetNode"]]
        ] = defaultdict(list)

        # Build the dependency graph of asset keys.
        all_keys = {node.asset_key for _, node in repo_handle_external_asset_nodes}
        upstream: Dict[AssetKey, Set[AssetKey]] = {key: set() for key in all_keys}
        downstream: Dict[AssetKey, Set[AssetKey]] = {key: set() for key in all_keys}

        for repo_handle, node in repo_handle_external_asset_nodes:
            repo_node_pairs_by_key[node.asset_key].append((repo_handle, node))
            for dep in node.dependencies:
                upstream[node.asset_key].add(dep.upstream_asset_key)
                downstream[dep.upstream_asset_key].add(node.asset_key)

        dep_graph: DependencyGraph[AssetKey] = {"upstream": upstream, "downstream": downstream}

        check_keys_by_asset_key: Dict[AssetKey, Set[AssetCheckKey]] = defaultdict(set)
        for c in external_asset_checks:
            check_keys_by_asset_key[c.asset_key].add(c.key)

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

        # Build the set of ExternalAssetChecks, indexed by key. Also the index of execution units for
        # each asset check key.
        asset_checks_by_key: Dict[AssetCheckKey, "ExternalAssetCheck"] = {}
        for asset_check in external_asset_checks:
            asset_checks_by_key[asset_check.key] = asset_check
        asset_check_execution_sets_by_key = {
            k: v for k, v in execution_sets_by_key.items() if isinstance(k, AssetCheckKey)
        }

        return cls(
            asset_nodes_by_key,
            asset_checks_by_key,
            asset_check_execution_sets_by_key,
        )

    ##### COMMON ASSET GRAPH INTERFACE

    def get_execution_set_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            return self.get(asset_or_check_key).execution_set_asset_and_check_keys
        else:  # AssetCheckKey
            return self._asset_check_execution_sets_by_key[asset_or_check_key]

    ##### REMOTE-SPECIFIC METHODS

    @property
    def external_asset_nodes_by_key(self) -> Mapping[AssetKey, "ExternalAssetNode"]:
        # This exists to support existing callsites but it should be removed ASAP, since it exposes
        # `ExternalAssetNode` instances directly. All sites using this should use RemoteAssetNode
        # instead.
        return {k: node._priority_node for k, node in self._asset_nodes_by_key.items()}  # noqa: SLF001

    @property
    def asset_checks(self) -> Sequence["ExternalAssetCheck"]:
        return list(dict.fromkeys(self._asset_checks_by_key.values()))

    @cached_property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return {key for asset in self.asset_nodes for key in asset.check_keys}

    def asset_keys_for_job(self, job_name: str) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if job_name in node.job_names}

    @cached_property
    def all_job_names(self) -> AbstractSet[str]:
        return {job_name for node in self.asset_nodes for job_name in node.job_names}

    @cached_property
    def repository_handles_by_key(self) -> Mapping[AssetKey, RepositoryHandle]:
        return {k: node.priority_repository_handle for k, node in self._asset_nodes_by_key.items()}

    def get_repository_handle(self, asset_key: AssetKey) -> RepositoryHandle:
        return self.get(asset_key).priority_repository_handle

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
        external_repo: Optional[ExternalRepository],
    ) -> Optional[str]:
        """Returns the name of the asset base job that contains all the given assets, or None if there is no such
        job.

        Note: all asset_keys should be in the same repository.
        """
        return IMPLICIT_ASSET_JOB_NAME

    def split_asset_keys_by_repository(
        self, asset_keys: AbstractSet[AssetKey]
    ) -> Sequence[AbstractSet[AssetKey]]:
        asset_keys_by_repo = defaultdict(set)
        for asset_key in asset_keys:
            repo_handle = self.get_repository_handle(asset_key)
            asset_keys_by_repo[(repo_handle.location_name, repo_handle.repository_name)].add(
                asset_key
            )
        return list(asset_keys_by_repo.values())


def _warn_on_duplicate_nodes(
    repo_handle_external_asset_nodes: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
) -> None:
    # Split the nodes into materializable, observable, and unexecutable nodes. Observable and
    # unexecutable `ExternalAssetNode` represent both source and external assets-- the
    # "External" in "ExternalAssetNode" is unrelated to the "external" in "external asset", this
    # is just an unfortunate naming collision. `ExternalAssetNode` will be renamed eventually.
    materializable_node_pairs: List[Tuple[RepositoryHandle, "ExternalAssetNode"]] = []
    observable_node_pairs: List[Tuple[RepositoryHandle, "ExternalAssetNode"]] = []
    unexecutable_node_pairs: List[Tuple[RepositoryHandle, "ExternalAssetNode"]] = []
    for repo_handle, node in repo_handle_external_asset_nodes:
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
    node_pairs: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
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
    external_asset_nodes: Iterable["ExternalAssetNode"],
    external_asset_checks: Iterable["ExternalAssetCheck"],
) -> Mapping[AssetKeyOrCheckKey, AbstractSet[AssetKeyOrCheckKey]]:
    from dagster._core.remote_representation.external_data import ExternalAssetNode

    all_items = [*external_asset_nodes, *external_asset_checks]

    execution_sets_by_id: Dict[str, Set[AssetKeyOrCheckKey]] = defaultdict(set)
    for item in all_items:
        id = item.execution_set_identifier
        key = item.asset_key if isinstance(item, ExternalAssetNode) else item.key
        if id is not None:
            execution_sets_by_id[id].add(key)

    execution_sets_by_key: Dict[AssetKeyOrCheckKey, Set[AssetKeyOrCheckKey]] = {}
    for item in all_items:
        id = item.execution_set_identifier
        key = item.asset_key if isinstance(item, ExternalAssetNode) else item.key
        execution_sets_by_key[key] = execution_sets_by_id[id] if id is not None else {key}

    return execution_sets_by_key
