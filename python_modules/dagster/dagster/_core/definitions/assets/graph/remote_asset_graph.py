import itertools
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from functools import cached_property
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Annotated,
    Generic,
    Optional,
    TypeVar,
    Union,
)

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    AssetExecutionType,
)
from dagster._core.definitions.assets.graph.base_asset_graph import (
    AssetCheckNode,
    AssetKey,
    BaseAssetGraph,
    BaseAssetNode,
)
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping import PartitionMapping
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.handle import InstigatorHandle, RepositoryHandle
from dagster._core.workspace.workspace import CurrentWorkspace
from dagster._record import ImportFrom, record
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.remote_representation.external_data import AssetCheckNodeSnap, AssetNodeSnap


@whitelist_for_serdes
@record
class RemoteAssetCheckNode:
    handle: RepositoryHandle
    asset_check: Annotated[
        "AssetCheckNodeSnap",
        ImportFrom("dagster._core.remote_representation.external_data"),
    ]
    execution_set_entity_keys: AbstractSet[EntityKey]


class RemoteAssetNode(BaseAssetNode, ABC):
    @abstractmethod
    def resolve_to_singular_repo_scoped_node(self) -> "RemoteRepositoryAssetNode": ...

    @property
    def execution_set_asset_keys(self) -> AbstractSet[AssetKey]:
        return {k for k in self.execution_set_entity_keys if isinstance(k, AssetKey)}

    @property
    def description(self) -> Optional[str]:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.description

    @property
    def group_name(self) -> str:
        return (
            self.resolve_to_singular_repo_scoped_node().asset_node_snap.group_name
            or DEFAULT_GROUP_NAME
        )

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.metadata

    @property
    def execution_type(self) -> AssetExecutionType:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.execution_type

    @property
    def pools(self) -> Optional[set[str]]:
        return self.resolve_to_singular_repo_scoped_node().pools

    @property
    def tags(self) -> Mapping[str, str]:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.tags or {}

    @property
    def owners(self) -> Sequence[str]:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.owners or []

    @property
    def is_partitioned(self) -> bool:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.partitions is not None

    @cached_property
    def partitions_def(self) -> Optional[PartitionsDefinition]:  # pyright: ignore[reportIncompatibleMethodOverride]
        partitions_snap = self.resolve_to_singular_repo_scoped_node().asset_node_snap.partitions
        return partitions_snap.get_partitions_definition() if partitions_snap else None

    @property
    def legacy_freshness_policy(self) -> Optional[LegacyFreshnessPolicy]:
        # It is currently not possible to access the freshness policy for an observation definition
        # if a materialization definition also exists. This needs to be fixed.
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.legacy_freshness_policy

    @property
    def freshness_policy(self) -> Optional[InternalFreshnessPolicy]:
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.freshness_policy

    @property
    def code_version(self) -> Optional[str]:
        # It is currently not possible to access the code version for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return self.resolve_to_singular_repo_scoped_node().asset_node_snap.code_version

    @property
    def job_names(self) -> Sequence[str]:
        # It is currently not possible to access the job names for an observation definition if a
        # materialization definition also exists. This needs to be fixed.
        return (
            self.resolve_to_singular_repo_scoped_node().asset_node_snap.job_names
            if self.is_executable
            else []
        )


@whitelist_for_serdes
@record
class RemoteRepositoryAssetNode(RemoteAssetNode):
    """Asset nodes from a single RemoteRepository."""

    repository_handle: RepositoryHandle
    asset_node_snap: Annotated[
        "AssetNodeSnap",
        ImportFrom("dagster._core.remote_representation.external_data"),
    ]
    parent_keys: AbstractSet[AssetKey]
    child_keys: AbstractSet[AssetKey]
    check_keys: AbstractSet[AssetCheckKey]  # pyright: ignore[reportIncompatibleMethodOverride]
    execution_set_entity_keys: AbstractSet[EntityKey]  # pyright: ignore[reportIncompatibleMethodOverride]

    def __hash__(self):
        # we create sets of these objects in the context of asset graphs but don't want to
        # enforce that all recursively contained types are hashable so use object hash instead
        return object.__hash__(self)

    def resolve_to_singular_repo_scoped_node(self) -> "RemoteRepositoryAssetNode":
        return self

    @property
    def key(self) -> AssetKey:  # pyright: ignore[reportIncompatibleVariableOverride]
        return self.asset_node_snap.asset_key

    @property
    def is_materializable(self) -> bool:
        return self.asset_node_snap.is_materializable

    @property
    def is_observable(self) -> bool:
        return self.asset_node_snap.is_observable

    @property
    def is_external(self) -> bool:
        return self.asset_node_snap.is_external

    @property
    def is_executable(self) -> bool:
        return self.asset_node_snap.is_executable

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return {
            dep.parent_asset_key: dep.partition_mapping
            for dep in self.asset_node_snap.parent_edges
            if dep.partition_mapping is not None
        }

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self.asset_node_snap.backfill_policy

    @property
    def automation_condition(self) -> Optional[AutomationCondition]:
        return self.asset_node_snap.automation_condition

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self.asset_node_snap.auto_materialize_policy

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return self.asset_node_snap.auto_observe_interval_minutes

    @property
    def pools(self) -> Optional[set[str]]:
        return self.asset_node_snap.pools


@whitelist_for_serdes
@record
class RepositoryScopedAssetInfo:
    """RemoteRepositoryAssetNode paired with additional information from that repository.
    This split allows repository scoped asset graph to be constructed without depending on schedules/sensors
    as defining schedule/sensors needs an asset graph.
    """

    asset_node: RemoteRepositoryAssetNode
    targeting_sensor_names: Sequence[str]
    targeting_schedule_names: Sequence[str]

    @property
    def handle(self) -> RepositoryHandle:
        return self.asset_node.repository_handle


@whitelist_for_serdes
@record
class RemoteWorkspaceAssetNode(RemoteAssetNode):
    """Asset nodes constructed from a CurrentWorkspace, containing nodes from potentially several RemoteRepositories."""

    repo_scoped_asset_infos: Sequence[RepositoryScopedAssetInfo]

    def __hash__(self):
        # we create sets of these objects in the context of asset graphs but don't want to
        # enforce that all recursively contained types are hashable so use object hash instead
        return object.__hash__(self)

    ##### COMMON ASSET NODE INTERFACE
    @cached_property
    def key(self) -> AssetKey:  # pyright: ignore[reportIncompatibleVariableOverride]
        return self.repo_scoped_asset_infos[0].asset_node.asset_node_snap.asset_key

    ### KEEP THIS IN SYNC WITH THE JS CODE THAT MERGES THE SDA DEFINITIONS: https://github.com/dagster-io/dagster/blob/22e79ea7024bd13b197e3a2f66401197badceb75/js_modules/dagster-ui/packages/ui-core/src/assets/useAllAssets.tsx#L239-L256
    @property
    def parent_keys(self) -> AbstractSet[AssetKey]:  # pyright: ignore[reportIncompatibleVariableOverride]
        # combine deps from all nodes
        keys = set()
        for info in self.repo_scoped_asset_infos:
            keys.update(info.asset_node.parent_keys)
        return keys

    @property
    def child_keys(self) -> AbstractSet[AssetKey]:  # pyright: ignore[reportIncompatibleVariableOverride]
        # combine deps from all nodes
        keys = set()
        for info in self.repo_scoped_asset_infos:
            keys.update(info.asset_node.child_keys)
        return keys

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        # combine check keys from all nodes
        keys = set()
        for info in self.repo_scoped_asset_infos:
            keys.update(info.asset_node.check_keys)
        return keys

    @property
    def execution_set_entity_keys(
        self,
    ) -> AbstractSet[Union[AssetKey, AssetCheckKey]]:
        return self.resolve_to_singular_repo_scoped_node().execution_set_entity_keys

    @cached_property
    def is_materializable(self) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return any(info.asset_node.is_materializable for info in self.repo_scoped_asset_infos)

    @cached_property
    def is_observable(self) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return any(info.asset_node.is_observable for info in self.repo_scoped_asset_infos)

    @cached_property
    def is_external(self) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return all(info.asset_node.is_external for info in self.repo_scoped_asset_infos)

    @cached_property
    def is_executable(self) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return any(node.asset_node.is_executable for node in self.repo_scoped_asset_infos)

    @cached_property
    def pools(self) -> Optional[set[str]]:  # pyright: ignore[reportIncompatibleMethodOverride]
        pools = set()
        for info in self.repo_scoped_asset_infos:
            pools.update(info.asset_node.pools or set())
        return pools

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.is_materializable:
            return {
                dep.parent_asset_key: dep.partition_mapping
                for dep in self._materializable_node_snap.parent_edges
                if dep.partition_mapping is not None
            }
        else:
            return {}

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

    ##### REMOTE-SPECIFIC INTERFACE
    @cached_method
    def resolve_to_singular_repo_scoped_node(self) -> "RemoteRepositoryAssetNode":
        # Return a materialization node if it exists, otherwise return an observable node if it
        # exists, otherwise return any non-stub node, otherwise return any node.
        # This exists to preserve implicit behavior, where the
        # materialization node was previously preferred over the observable node. This is a
        # temporary measure until we can appropriately scope the accessors that could apply to
        # either a materialization or observation node.
        # This property supports existing behavior but it should be phased out, because it relies on
        # materialization nodes shadowing observation nodes that would otherwise be exposed.
        return next(
            itertools.chain(
                (
                    info.asset_node
                    for info in self.repo_scoped_asset_infos
                    if info.asset_node.is_materializable
                ),
                (
                    info.asset_node
                    for info in self.repo_scoped_asset_infos
                    if info.asset_node.is_observable
                ),
                (
                    info.asset_node
                    for info in self.repo_scoped_asset_infos
                    if not info.asset_node.metadata.get(SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET)
                ),
                (info.asset_node for info in self.repo_scoped_asset_infos),
            )
        )

    def get_targeting_schedule_handles(
        self,
    ) -> Sequence[InstigatorHandle]:
        selectors = []
        for node in self.repo_scoped_asset_infos:
            for schedule_name in node.targeting_schedule_names:
                selectors.append(
                    InstigatorHandle(
                        repository_handle=node.handle,
                        instigator_name=schedule_name,
                    )
                )

        return selectors

    def get_targeting_sensor_handles(
        self,
    ) -> Sequence[InstigatorHandle]:
        selectors = []
        for node in self.repo_scoped_asset_infos:
            for sensor_name in node.targeting_sensor_names:
                selectors.append(
                    InstigatorHandle(
                        repository_handle=node.handle,
                        instigator_name=sensor_name,
                    )
                )
        return selectors

    ##### HELPERS

    @cached_property
    def _materializable_node_snap(self) -> "AssetNodeSnap":
        try:
            return next(
                info.asset_node.asset_node_snap
                for info in self.repo_scoped_asset_infos
                if info.asset_node.is_materializable
            )
        except StopIteration:
            check.failed("No materializable node found")

    @cached_property
    def _observable_node_snap(self) -> "AssetNodeSnap":
        try:
            return next(
                info.asset_node.asset_node_snap
                for info in self.repo_scoped_asset_infos
                if info.asset_node.is_observable
            )
        except StopIteration:
            check.failed("No observable node found")


TRemoteAssetNode = TypeVar("TRemoteAssetNode", bound=RemoteAssetNode)


class RemoteAssetGraph(BaseAssetGraph[TRemoteAssetNode], ABC, Generic[TRemoteAssetNode]):
    @property
    @abstractmethod
    def remote_asset_nodes_by_key(self) -> Mapping[AssetKey, TRemoteAssetNode]: ...

    @property
    @abstractmethod
    def remote_asset_check_nodes_by_key(
        self,
    ) -> Mapping[AssetCheckKey, RemoteAssetCheckNode]: ...

    ##### COMMON ASSET GRAPH INTERFACE
    @cached_property
    def _asset_check_nodes_by_key(self) -> Mapping[AssetCheckKey, AssetCheckNode]:  # pyright: ignore[reportIncompatibleVariableOverride]
        return {
            k: AssetCheckNode(
                k,
                v.asset_check.additional_asset_keys,
                v.asset_check.blocking,
                v.asset_check.description,
                v.asset_check.automation_condition,
                {},  # metadata not yet on AssetCheckNodeSnap
            )
            for k, v in self.remote_asset_check_nodes_by_key.items()
        }

    def get_execution_set_asset_and_check_keys(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, entity_key: EntityKey
    ) -> AbstractSet[EntityKey]:
        if isinstance(entity_key, AssetKey):
            return self.get(entity_key).execution_set_entity_keys
        else:  # AssetCheckKey
            return self.remote_asset_check_nodes_by_key[entity_key].execution_set_entity_keys

    ##### REMOTE-SPECIFIC METHODS

    @property
    def asset_checks(self) -> Sequence["AssetCheckNodeSnap"]:
        return [node.asset_check for node in self.remote_asset_check_nodes_by_key.values()]

    @cached_property
    def _asset_check_nodes_by_asset_key(self) -> Mapping[AssetKey, Sequence[RemoteAssetCheckNode]]:
        by_asset_key = {}
        for node in self.remote_asset_check_nodes_by_key.values():
            by_asset_key.setdefault(node.asset_check.asset_key, []).append(node)
        return by_asset_key

    def get_checks_for_asset(self, asset_key: AssetKey) -> Sequence[RemoteAssetCheckNode]:
        return self._asset_check_nodes_by_asset_key.get(asset_key, [])

    def get_check_keys_for_assets(
        self, asset_keys: AbstractSet[AssetKey]
    ) -> AbstractSet[AssetCheckKey]:
        return (
            set().union(
                *(
                    {check.asset_check.key for check in self.get_checks_for_asset(asset_key)}
                    for asset_key in asset_keys
                )
            )
            if asset_keys
            else set()
        )

    @cached_property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return set(self.remote_asset_check_nodes_by_key.keys())

    def asset_keys_for_job(self, job_name: str) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if job_name in node.job_names}

    @cached_property
    def all_job_names(self) -> AbstractSet[str]:
        return {job_name for node in self.asset_nodes for job_name in node.job_names}

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
        remote_repo: Optional[RemoteRepository],
    ) -> Optional[str]:
        """Returns the name of the asset base job that contains all the given assets, or None if there is no such
        job.

        Note: all asset_keys should be in the same repository.
        """
        return IMPLICIT_ASSET_JOB_NAME


@record
class RemoteRepositoryAssetGraph(RemoteAssetGraph[RemoteRepositoryAssetNode]):
    remote_asset_nodes_by_key: Mapping[AssetKey, RemoteRepositoryAssetNode]  # pyright: ignore[reportIncompatibleMethodOverride]
    remote_asset_check_nodes_by_key: Mapping[AssetCheckKey, RemoteAssetCheckNode]  # pyright: ignore[reportIncompatibleMethodOverride]

    @property
    def _asset_nodes_by_key(self) -> Mapping[AssetKey, RemoteRepositoryAssetNode]:  # pyright: ignore[reportIncompatibleVariableOverride]
        return self.remote_asset_nodes_by_key

    @classmethod
    def build(cls, repo: RemoteRepository):
        # First pass, we need to:

        # * Build the dependency graph of asset keys.
        upstream: dict[AssetKey, set[AssetKey]] = defaultdict(set)
        downstream: dict[AssetKey, set[AssetKey]] = defaultdict(set)

        # * Build an index of execution sets by key. An execution set is a set of assets and checks
        # that must be executed together. AssetNodeSnaps and AssetCheckNodeSnaps already have an
        # optional execution_set_identifier set. A null execution_set_identifier indicates that the
        # node or check can be executed independently.
        execution_sets_by_id: dict[str, set[EntityKey]] = defaultdict(set)

        # * Map checks to their corresponding asset keys
        check_keys_by_asset_key: dict[AssetKey, set[AssetCheckKey]] = defaultdict(set)
        for asset_snap in repo.get_asset_node_snaps():
            id = asset_snap.execution_set_identifier
            key = asset_snap.asset_key
            if id is not None:
                execution_sets_by_id[id].add(key)

            for dep in asset_snap.parent_edges:
                upstream[asset_snap.asset_key].add(dep.parent_asset_key)
                downstream[dep.parent_asset_key].add(asset_snap.asset_key)

        for check_snap in repo.get_asset_check_node_snaps():
            id = check_snap.execution_set_identifier
            key = check_snap.key
            if id is not None:
                execution_sets_by_id[id].add(key)

            check_keys_by_asset_key[check_snap.asset_key].add(check_snap.key)

        # Second Pass - build the final nodes
        assets_by_key: dict[AssetKey, RemoteRepositoryAssetNode] = {}
        asset_checks_by_key: dict[AssetCheckKey, RemoteAssetCheckNode] = {}

        for asset_snap in repo.get_asset_node_snaps():
            id = asset_snap.execution_set_identifier
            key = asset_snap.asset_key

            assets_by_key[key] = RemoteRepositoryAssetNode(
                repository_handle=repo.handle,
                asset_node_snap=asset_snap,
                execution_set_entity_keys=execution_sets_by_id[id] if id is not None else {key},
                parent_keys=upstream[key],
                child_keys=downstream[key],
                check_keys=check_keys_by_asset_key[key],
            )

        for check_snap in repo.get_asset_check_node_snaps():
            id = check_snap.execution_set_identifier
            key = check_snap.key

            asset_checks_by_key[key] = RemoteAssetCheckNode(
                handle=repo.handle,
                asset_check=check_snap,
                execution_set_entity_keys=execution_sets_by_id[id] if id is not None else {key},
            )

        return cls(
            remote_asset_nodes_by_key=assets_by_key,
            remote_asset_check_nodes_by_key=asset_checks_by_key,
        )

    @classmethod
    def empty(cls):
        return cls(
            remote_asset_nodes_by_key={},
            remote_asset_check_nodes_by_key={},
        )


class RemoteWorkspaceAssetGraph(RemoteAssetGraph[RemoteWorkspaceAssetNode]):
    def __init__(
        self,
        remote_asset_nodes_by_key: Mapping[AssetKey, RemoteWorkspaceAssetNode],
        remote_asset_check_nodes_by_key: Mapping[AssetCheckKey, RemoteAssetCheckNode],
    ):
        self._remote_asset_nodes_by_key = remote_asset_nodes_by_key
        self._remote_asset_check_nodes_by_key = remote_asset_check_nodes_by_key

    @property
    def remote_asset_nodes_by_key(self) -> Mapping[AssetKey, RemoteWorkspaceAssetNode]:
        return self._remote_asset_nodes_by_key

    @property
    def remote_asset_check_nodes_by_key(
        self,
    ) -> Mapping[AssetCheckKey, RemoteAssetCheckNode]:
        return self._remote_asset_check_nodes_by_key

    @property
    def _asset_nodes_by_key(self) -> Mapping[AssetKey, RemoteWorkspaceAssetNode]:  # pyright: ignore[reportIncompatibleVariableOverride]
        return self.remote_asset_nodes_by_key

    @property
    def asset_node_snaps_by_key(self) -> Mapping[AssetKey, "AssetNodeSnap"]:
        # This exists to support existing callsites but it should be removed ASAP, since it exposes
        # `AssetNodeSnap` instances directly. All sites using this should use RemoteAssetNode
        # instead.
        return {
            k: node.resolve_to_singular_repo_scoped_node().asset_node_snap
            for k, node in self._asset_nodes_by_key.items()
        }

    @cached_property
    def repository_handles_by_key(self) -> Mapping[EntityKey, RepositoryHandle]:
        return {
            **{
                k: node.resolve_to_singular_repo_scoped_node().repository_handle
                for k, node in self._asset_nodes_by_key.items()
            },
            **{k: v.handle for k, v in self.remote_asset_check_nodes_by_key.items()},
        }

    def get_repository_handle(self, key: EntityKey) -> RepositoryHandle:
        if isinstance(key, AssetKey):
            return self.get(key).resolve_to_singular_repo_scoped_node().repository_handle
        else:
            return self.remote_asset_check_nodes_by_key[key].handle

    def split_entity_keys_by_repository(
        self, keys: AbstractSet[EntityKey]
    ) -> Sequence[AbstractSet[EntityKey]]:
        keys_by_repo = defaultdict(set)
        for key in keys:
            repo_handle = self.get_repository_handle(key)
            keys_by_repo[(repo_handle.location_name, repo_handle.repository_name)].add(key)
        return list(keys_by_repo.values())

    @classmethod
    def build(cls, workspace: CurrentWorkspace):
        # Combine repository scoped asset graphs with additional context to form the global graph

        code_locations = sorted(
            (
                location_entry.code_location
                for location_entry in workspace.code_location_entries.values()
                if location_entry.code_location
            ),
            key=lambda code_location: code_location.name,
        )
        repos = (
            repo
            for code_location in code_locations
            for repo in sorted(
                code_location.get_repositories().values(), key=lambda repo: repo.name
            )
        )

        asset_infos_by_key: dict[AssetKey, list[RepositoryScopedAssetInfo]] = defaultdict(list)
        asset_checks_by_key: dict[AssetCheckKey, RemoteAssetCheckNode] = {}
        for repo in repos:
            for key, asset_node in repo.asset_graph.remote_asset_nodes_by_key.items():
                asset_infos_by_key[key].append(
                    RepositoryScopedAssetInfo(
                        asset_node=asset_node,
                        targeting_sensor_names=sorted(
                            s.name for s in repo.get_sensors_targeting(asset_node.key)
                        ),
                        targeting_schedule_names=sorted(
                            s.name for s in repo.get_schedules_targeting(asset_node.key)
                        ),
                    )
                )
            # NOTE: matches previous behavior of completely ignoring asset check collisions
            asset_checks_by_key.update(repo.asset_graph.remote_asset_check_nodes_by_key)

        asset_nodes_by_key = {}
        nodes_with_multiple = []
        for key, asset_infos in asset_infos_by_key.items():
            node = RemoteWorkspaceAssetNode(
                repo_scoped_asset_infos=asset_infos,
            )
            asset_nodes_by_key[key] = node
            if len(asset_infos) > 1:
                nodes_with_multiple.append(node)

        _warn_on_duplicate_nodes(nodes_with_multiple)

        return cls(
            remote_asset_nodes_by_key=asset_nodes_by_key,
            remote_asset_check_nodes_by_key=asset_checks_by_key,
        )


def _warn_on_duplicate_nodes(
    nodes_with_multiple: Sequence[RemoteWorkspaceAssetNode],
) -> None:
    # Split the nodes into materializable, observable, and unexecutable nodes. Observable and
    # unexecutable `AssetNodeSnap` represent both source and external assets-- the
    # "External" in "AssetNodeSnap" is unrelated to the "external" in "external asset", this
    # is just an unfortunate naming collision. `AssetNodeSnap` will be renamed eventually.
    materializable_duplicates: Mapping[AssetKey, Sequence[str]] = {}
    observable_duplicates: Mapping[AssetKey, Sequence[str]] = {}
    for node in nodes_with_multiple:
        check.invariant(
            len(node.repo_scoped_asset_infos) > 1,
            "only perform check on nodes with multiple defs",
        )
        observable_locations = []
        materializable_locations = []
        for info in node.repo_scoped_asset_infos:
            snap = info.asset_node.asset_node_snap
            location = info.asset_node.repository_handle.location_name
            if snap.is_source and snap.is_observable:
                observable_locations.append(location)
            elif snap.is_materializable:
                materializable_locations.append(location)
        if len(observable_locations) > 1:
            observable_duplicates[node.key] = observable_locations
        if len(materializable_locations) > 1:
            materializable_duplicates[node.key] = materializable_locations

    # It is possible for multiple nodes to exist that share the same key. This is invalid if
    # more than one node is materializable or if more than one node is observable. It is valid
    # if there is at most one materializable node and at most one observable node, with all
    # other nodes unexecutable.
    _warn_on_duplicates_within_subset(materializable_duplicates, AssetExecutionType.MATERIALIZATION)
    _warn_on_duplicates_within_subset(observable_duplicates, AssetExecutionType.OBSERVATION)


def _warn_on_duplicates_within_subset(
    duplicates: Mapping[AssetKey, Sequence[str]],
    execution_type: AssetExecutionType,
) -> None:
    if duplicates:
        duplicate_lines = []
        for asset_key, loc_names in duplicates.items():
            duplicate_lines.append(f"  {asset_key.to_string()}: {loc_names}")
        duplicate_str = "\n".join(duplicate_lines)

        warnings.warn(
            f"Found {execution_type.value} nodes for some asset keys in multiple code locations."
            f" Only one {execution_type.value} node is allowed per asset key. Duplicates:\n {duplicate_str}"
        )
