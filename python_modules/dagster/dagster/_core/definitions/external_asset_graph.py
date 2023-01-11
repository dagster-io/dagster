from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.handle import RepositoryHandle
from dagster._core.selector.subset_selector import DependencyGraph
from dagster._core.workspace.workspace import IWorkspace

from .asset_graph import AssetGraph
from .events import AssetKey
from .freshness_policy import FreshnessPolicy
from .partition import PartitionsDefinition
from .partition_mapping import PartitionMapping

if TYPE_CHECKING:
    from dagster._core.host_representation.external_data import ExternalAssetNode


class ExternalAssetGraph(AssetGraph):
    def __init__(
        self,
        asset_dep_graph: DependencyGraph,
        source_asset_keys: AbstractSet[AssetKey],
        partitions_defs_by_key: Mapping[AssetKey, Optional[PartitionsDefinition]],
        partition_mappings_by_key: Mapping[AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]],
        group_names_by_key: Mapping[AssetKey, Optional[str]],
        freshness_policies_by_key: Mapping[AssetKey, Optional[FreshnessPolicy]],
        required_multi_asset_sets_by_key: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]],
        repo_handles_by_key: Mapping[AssetKey, RepositoryHandle],
        job_names_by_key: Mapping[AssetKey, Sequence[str]],
    ):
        super().__init__(
            asset_dep_graph=asset_dep_graph,
            source_asset_keys=source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            required_multi_asset_sets_by_key=required_multi_asset_sets_by_key,
        )
        self._repo_handles_by_key = repo_handles_by_key
        self._job_names_by_key = job_names_by_key

    @classmethod
    def from_workspace(cls, context: IWorkspace) -> "ExternalAssetGraph":
        repo_locations = (
            location_entry.repository_location
            for location_entry in context.get_workspace_snapshot().values()
            if location_entry.repository_location
        )
        repos = (
            repo
            for repo_location in repo_locations
            for repo in repo_location.get_repositories().values()
        )
        repo_handle_external_asset_nodes: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]] = [
            (repo.handle, external_asset_node)
            for repo in repos
            for external_asset_node in repo.get_external_asset_nodes()
        ]

        return cls.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes
        )

    @classmethod
    def from_external_repository(
        cls, external_repository: ExternalRepository
    ) -> "ExternalAssetGraph":
        return cls.from_repository_handles_and_external_asset_nodes(
            [
                (external_repository.handle, asset_node)
                for asset_node in external_repository.get_external_asset_nodes()
            ]
        )

    @classmethod
    def from_repository_handles_and_external_asset_nodes(
        cls,
        repo_handle_external_asset_nodes: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
    ) -> "ExternalAssetGraph":
        upstream = {}
        source_asset_keys = set()
        partitions_defs_by_key = {}
        partition_mappings_by_key: Dict[AssetKey, Dict[AssetKey, PartitionMapping]] = defaultdict(
            defaultdict
        )
        group_names_by_key = {}
        freshness_policies_by_key = {}
        asset_keys_by_atomic_execution_unit_id: Dict[str, Set[AssetKey]] = defaultdict(set)
        repo_handles_by_key = {
            node.asset_key: repo_handle
            for repo_handle, node in repo_handle_external_asset_nodes
            if not node.is_source
        }
        job_names_by_key = {
            node.asset_key: node.job_names
            for _, node in repo_handle_external_asset_nodes
            if not node.is_source
        }

        all_non_source_keys = {
            node.asset_key for _, node in repo_handle_external_asset_nodes if not node.is_source
        }

        for repo_handle, node in repo_handle_external_asset_nodes:
            if node.is_source:
                if node.asset_key in all_non_source_keys:
                    # one repo's source is another repo's non-source
                    continue

                source_asset_keys.add(node.asset_key)

            upstream[node.asset_key] = {dep.upstream_asset_key for dep in node.dependencies}
            for dep in node.dependencies:
                if dep.partition_mapping is not None:
                    partition_mappings_by_key[node.asset_key][
                        dep.upstream_asset_key
                    ] = dep.partition_mapping
            partitions_defs_by_key[node.asset_key] = (
                node.partitions_def_data.get_partitions_definition()
                if node.partitions_def_data
                else None
            )
            group_names_by_key[node.asset_key] = node.group_name
            freshness_policies_by_key[node.asset_key] = node.freshness_policy

            if node.atomic_execution_unit_id is not None:
                asset_keys_by_atomic_execution_unit_id[node.atomic_execution_unit_id].add(
                    node.asset_key
                )

        downstream: Dict[AssetKey, Set[AssetKey]] = defaultdict(set)
        for asset_key, upstream_keys in upstream.items():
            for upstream_key in upstream_keys:
                downstream[upstream_key].add(asset_key)

        required_multi_asset_sets_by_key: Dict[AssetKey, AbstractSet[AssetKey]] = {}
        for _, asset_keys in asset_keys_by_atomic_execution_unit_id.items():
            if len(asset_keys) > 1:
                for asset_key in asset_keys:
                    required_multi_asset_sets_by_key[asset_key] = asset_keys

        return cls(
            asset_dep_graph={"upstream": upstream, "downstream": downstream},
            source_asset_keys=source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            required_multi_asset_sets_by_key=required_multi_asset_sets_by_key,
            repo_handles_by_key=repo_handles_by_key,
            job_names_by_key=job_names_by_key,
        )

    @property
    def repository_handles_by_key(self) -> Mapping[AssetKey, RepositoryHandle]:
        return self._repo_handles_by_key

    def get_repository_handle(self, asset_key: AssetKey) -> RepositoryHandle:
        return self._repo_handles_by_key[asset_key]

    def get_job_names(self, asset_key: AssetKey) -> Iterable[str]:
        return self._job_names_by_key[asset_key]
