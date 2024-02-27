import warnings
from collections import defaultdict
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
    Tuple,
)

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.assets_job import ASSET_BASE_JOB_PREFIX
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.handle import RepositoryHandle
from dagster._core.selector.subset_selector import DependencyGraph
from dagster._core.workspace.workspace import IWorkspace
from dagster._utils.cached_method import cached_method

from .asset_graph import AssetGraph, AssetKeyOrCheckKey
from .backfill_policy import BackfillPolicy
from .events import AssetKey
from .freshness_policy import FreshnessPolicy
from .partition import PartitionsDefinition
from .partition_mapping import PartitionMapping

if TYPE_CHECKING:
    from dagster._core.host_representation.external_data import (
        ExternalAssetCheck,
        ExternalAssetNode,
    )


class ExternalAssetGraph(AssetGraph):
    def __init__(
        self,
        asset_nodes_by_key: Mapping[AssetKey, "ExternalAssetNode"],
        asset_checks_by_key: Mapping[AssetCheckKey, "ExternalAssetCheck"],
        repo_handles_by_key: Mapping[AssetKey, RepositoryHandle],
    ):
        self._asset_nodes_by_key = asset_nodes_by_key
        self._asset_checks_by_key = asset_checks_by_key
        self._repo_handles_by_key = repo_handles_by_key

    @classmethod
    def from_workspace(cls, context: IWorkspace) -> "ExternalAssetGraph":
        code_locations = (
            location_entry.code_location
            for location_entry in context.get_workspace_snapshot().values()
            if location_entry.code_location
        )
        repos = (
            repo
            for code_location in code_locations
            for repo in code_location.get_repositories().values()
        )
        repo_handle_external_asset_nodes: Sequence[
            Tuple[RepositoryHandle, "ExternalAssetNode"]
        ] = []
        asset_checks: Sequence["ExternalAssetCheck"] = []

        for repo in repos:
            for external_asset_node in repo.get_external_asset_nodes():
                repo_handle_external_asset_nodes.append((repo.handle, external_asset_node))

            asset_checks.extend(repo.get_external_asset_checks())

        return cls.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes=repo_handle_external_asset_nodes,
            external_asset_checks=asset_checks,
        )

    @classmethod
    def from_external_repository(
        cls, external_repository: ExternalRepository
    ) -> "ExternalAssetGraph":
        return cls.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes=[
                (external_repository.handle, asset_node)
                for asset_node in external_repository.get_external_asset_nodes()
            ],
            external_asset_checks=external_repository.get_external_asset_checks(),
        )

    @classmethod
    def from_repository_handles_and_external_asset_nodes(
        cls,
        repo_handle_external_asset_nodes: Sequence[Tuple[RepositoryHandle, "ExternalAssetNode"]],
        external_asset_checks: Sequence["ExternalAssetCheck"],
    ) -> "ExternalAssetGraph":
        repo_handles_by_key = {
            node.asset_key: repo_handle
            for repo_handle, node in repo_handle_external_asset_nodes
            if node.is_executable
        }

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

        asset_nodes_by_key = {}

        _warn_on_duplicate_nodes(materializable_node_pairs, AssetExecutionType.MATERIALIZATION)
        _warn_on_duplicate_nodes(observable_node_pairs, AssetExecutionType.OBSERVATION)

        # It is possible for multiple nodes to exist that share the same key. This is invalid if
        # more than one node is materializable or if more than one node is observable. It is valid
        # if there is at most one materializable node and at most one observable node, with all
        # other nodes unexecutable. The asset graph will receive only a single `ExternalAssetNode`
        # representing the asset. This will always be the materializable node if one exists; then
        # the observable node if it exists; then finally the first-encountered unexecutable node.
        for repo_handle, node in materializable_node_pairs:
            asset_nodes_by_key[node.asset_key] = node

        for repo_handle, node in observable_node_pairs:
            if node.asset_key in asset_nodes_by_key:
                current_node = asset_nodes_by_key[node.asset_key]
                asset_nodes_by_key[node.asset_key] = current_node._replace(is_observable=True)
            else:
                asset_nodes_by_key[node.asset_key] = node

        for repo_handle, node in unexecutable_node_pairs:
            if node.asset_key in asset_nodes_by_key:
                continue
            asset_nodes_by_key[node.asset_key] = node

        asset_checks_by_key: Dict[AssetCheckKey, "ExternalAssetCheck"] = {}
        for asset_check in external_asset_checks:
            asset_checks_by_key[asset_check.key] = asset_check

        return cls(
            asset_nodes_by_key,
            asset_checks_by_key,
            repo_handles_by_key=repo_handles_by_key,
        )

    @property
    def asset_nodes(self) -> Sequence["ExternalAssetNode"]:
        return list(self._asset_nodes_by_key.values())

    def get_asset_node(self, asset_key: AssetKey) -> "ExternalAssetNode":
        return self._asset_nodes_by_key[asset_key]

    def has_asset(self, asset_key: AssetKey) -> bool:
        return asset_key in self._asset_nodes_by_key

    @property
    def asset_checks(self) -> Sequence["ExternalAssetCheck"]:
        return list(self._asset_checks_by_key.values())

    def get_asset_check(self, asset_check_key: AssetCheckKey) -> "ExternalAssetCheck":
        return self._asset_checks_by_key[asset_check_key]

    @property
    @cached_method
    def asset_dep_graph(self) -> DependencyGraph[AssetKey]:
        upstream = {node.asset_key: set() for node in self.asset_nodes}
        downstream = {node.asset_key: set() for node in self.asset_nodes}
        for node in self.asset_nodes:
            for dep in node.dependencies:
                upstream[node.asset_key].add(dep.upstream_asset_key)
                downstream[dep.upstream_asset_key].add(node.asset_key)
        return {"upstream": upstream, "downstream": downstream}

    @property
    @cached_method
    def all_asset_keys(self) -> AbstractSet[AssetKey]:
        return {node.asset_key for node in self.asset_nodes}

    @property
    @cached_method
    def materializable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {
            node.asset_key
            for node in self.asset_nodes
            if node.execution_type == AssetExecutionType.MATERIALIZATION
        }

    def is_materializable(self, asset_key: AssetKey) -> bool:
        return self.get_asset_node(asset_key).execution_type == AssetExecutionType.MATERIALIZATION

    @property
    @cached_method
    def observable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {
            node.asset_key
            for node in self.asset_nodes
            # check the separate `is_observable` field because `execution_type` will be
            # `MATERIALIZATION` if there exists a materializable version of the asset
            if node.is_observable
        }

    def is_observable(self, asset_key: AssetKey) -> bool:
        return self.get_asset_node(asset_key).is_observable

    @property
    @cached_method
    def external_asset_keys(self) -> AbstractSet[AssetKey]:
        return {
            node.asset_key
            for node in self.asset_nodes
            if node.execution_type != AssetExecutionType.MATERIALIZATION
        }

    def is_external(self, asset_key: AssetKey) -> bool:
        return self.get_asset_node(asset_key).execution_type != AssetExecutionType.MATERIALIZATION

    @property
    @cached_method
    def executable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {node.asset_key for node in self.asset_nodes if node.is_executable}

    def is_executable(self, asset_key: AssetKey) -> bool:
        return self.get_asset_node(asset_key).execution_type != AssetExecutionType.UNEXECUTABLE

    def asset_keys_for_group(self, group_name: str) -> AbstractSet[AssetKey]:
        return {node.asset_key for node in self.asset_nodes if node.group_name == group_name}

    def asset_keys_for_job(self, job_name: str) -> AbstractSet[AssetKey]:
        return {node.asset_key for node in self.asset_nodes if job_name in node.job_names}

    def get_required_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            atomic_execution_unit_id = self.get_asset_node(
                asset_or_check_key
            ).atomic_execution_unit_id
        else:  # AssetCheckKey
            atomic_execution_unit_id = self.get_asset_check(
                asset_or_check_key
            ).atomic_execution_unit_id
        if atomic_execution_unit_id is None:
            return set()
        else:
            return {
                *(
                    node.asset_key
                    for node in self.asset_nodes
                    if node.atomic_execution_unit_id == atomic_execution_unit_id
                ),
                *(
                    node.key
                    for node in self.asset_checks
                    if node.atomic_execution_unit_id == atomic_execution_unit_id
                ),
            }

    def get_required_multi_asset_keys(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        return {
            key
            for key in self.get_required_asset_and_check_keys(asset_key)
            if isinstance(key, AssetKey)
        }

    @property
    @cached_method
    def all_job_names(self) -> AbstractSet[str]:
        return {job_name for node in self.asset_nodes for job_name in node.job_names}

    @property
    @cached_method
    def all_group_names(self) -> AbstractSet[str]:
        return {node.group_name for node in self.asset_nodes if node.group_name}

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        external_def = self.get_asset_node(asset_key).partitions_def_data
        return external_def.get_partitions_definition() if external_def else None

    def get_partition_mappings(
        self, asset_key: AssetKey
    ) -> Optional[Mapping[AssetKey, PartitionMapping]]:
        return {
            dep.upstream_asset_key: dep.partition_mapping
            for dep in self.get_asset_node(asset_key).dependencies
            if dep.partition_mapping is not None
        }

    def get_group_name(self, asset_key: AssetKey) -> Optional[str]:
        return self.get_asset_node(asset_key).group_name

    def get_freshness_policy(self, asset_key: AssetKey) -> Optional[FreshnessPolicy]:
        return self.get_asset_node(asset_key).freshness_policy

    def get_auto_materialize_policy(self, asset_key: AssetKey) -> Optional[AutoMaterializePolicy]:
        return self.get_asset_node(asset_key).auto_materialize_policy

    def get_auto_observe_interval_minutes(self, asset_key: AssetKey) -> Optional[float]:
        return self.get_asset_node(asset_key).auto_observe_interval_minutes

    def get_backfill_policy(self, asset_key: AssetKey) -> Optional[BackfillPolicy]:
        return self.get_asset_node(asset_key).backfill_policy

    def get_code_version(self, asset_key: AssetKey) -> Optional[str]:
        return self.get_asset_node(asset_key).code_version

    @property
    def repository_handles_by_key(self) -> Mapping[AssetKey, RepositoryHandle]:
        return self._repo_handles_by_key

    def get_repository_handle(self, asset_key: AssetKey) -> RepositoryHandle:
        return self._repo_handles_by_key[asset_key]

    def get_materialization_job_names(self, asset_key: AssetKey) -> Sequence[str]:
        """Returns the names of jobs that materialize this asset."""
        return self.get_asset_node(asset_key).job_names

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
        if all(self.is_observable(asset_key) for asset_key in asset_keys):
            if external_repo is None:
                check.failed(
                    "external_repo must be passed in when getting job names for observable assets"
                )
            # for observable assets, we need to select the job based on the partitions def
            target_partitions_defs = {
                self.get_partitions_def(asset_key) for asset_key in asset_keys
            }
            check.invariant(len(target_partitions_defs) == 1, "Expected exactly one partitions def")
            target_partitions_def = next(iter(target_partitions_defs))

            # create a mapping from job name to the partitions def of that job
            partitions_def_by_job_name = {}
            for (
                external_partition_set_data
            ) in external_repo.external_repository_data.external_partition_set_datas:
                if external_partition_set_data.external_partitions_data is None:
                    partitions_def = None
                else:
                    partitions_def = external_partition_set_data.external_partitions_data.get_partitions_definition()
                partitions_def_by_job_name[external_partition_set_data.job_name] = partitions_def
            # add any jobs that don't have a partitions def
            for external_job in external_repo.get_all_external_jobs():
                job_name = external_job.external_job_data.name
                if job_name not in partitions_def_by_job_name:
                    partitions_def_by_job_name[job_name] = None
            # find the job that matches the expected partitions definition
            for job_name, external_partitions_def in partitions_def_by_job_name.items():
                asset_keys_for_job = self.asset_keys_for_job(job_name)
                if not job_name.startswith(ASSET_BASE_JOB_PREFIX):
                    continue
                if (
                    # unpartitioned observable assets may be materialized in any job
                    target_partitions_def is None
                    or external_partitions_def == target_partitions_def
                ) and all(asset_key in asset_keys_for_job for asset_key in asset_keys):
                    return job_name
        else:
            for job_name in self.all_job_names:
                asset_keys_for_job = self.asset_keys_for_job(job_name)
                if not job_name.startswith(ASSET_BASE_JOB_PREFIX):
                    continue
                if all(asset_key in self.asset_keys_for_job(job_name) for asset_key in asset_keys):
                    return job_name
        return None

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
