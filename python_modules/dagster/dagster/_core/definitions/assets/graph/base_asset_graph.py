from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import datetime
from functools import cached_property
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Generic,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_key import AssetKey, EntityKey, T_EntityKey
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping import PartitionMapping, UpstreamPartitionsResult
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.definitions.partitions.utils import (
    get_time_partition_key,
    get_time_partitions_def,
    infer_partition_mapping,
)
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.selector.subset_selector import DependencyGraph, fetch_sources
from dagster._core.utils import toposort
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
    from dagster._core.definitions.declarative_automation.automation_condition import (
        AutomationCondition,
    )


class ParentsPartitionsResult(NamedTuple):
    """Represents the result of mapping an asset partition to its upstream parent partitions.

    parent_partitions (AbstractSet[AssetKeyPartitionKey]): The existent parent partitions that are
        upstream of the asset partition. Filters out nonexistent partitions.
    required_but_nonexistent_parents_partitions (AbstractSet[AssetKeyPartitionKey]): The required
        upstream asset partitions that were mapped to but do not exist.
    """

    parent_partitions: AbstractSet[AssetKeyPartitionKey]
    required_but_nonexistent_parents_partitions: AbstractSet[AssetKeyPartitionKey]


class BaseEntityNode(ABC, Generic[T_EntityKey]):
    key: T_EntityKey

    @property
    @abstractmethod
    def partitions_def(self) -> Optional[PartitionsDefinition]: ...

    @property
    @abstractmethod
    def partition_mappings(self) -> Mapping[EntityKey, PartitionMapping]: ...

    @property
    @abstractmethod
    def automation_condition(self) -> Optional["AutomationCondition[T_EntityKey]"]: ...

    @property
    @abstractmethod
    def parent_entity_keys(self) -> AbstractSet[EntityKey]: ...

    @property
    @abstractmethod
    def child_entity_keys(self) -> AbstractSet[EntityKey]: ...

    @property
    @abstractmethod
    def description(self) -> Optional[str]: ...


class BaseAssetNode(BaseEntityNode[AssetKey]):
    key: AssetKey
    parent_keys: AbstractSet[AssetKey]
    child_keys: AbstractSet[AssetKey]

    @property
    def parent_entity_keys(self) -> AbstractSet[AssetKey]:
        return self.parent_keys

    @property
    def child_entity_keys(self) -> AbstractSet[EntityKey]:
        return self.child_keys | self.check_keys

    @property
    def has_self_dependency(self) -> bool:
        return self.key in self.parent_keys

    @property
    @abstractmethod
    def description(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def group_name(self) -> str: ...

    @property
    @abstractmethod
    def is_materializable(self) -> bool: ...

    @property
    @abstractmethod
    def is_observable(self) -> bool: ...

    @property
    @abstractmethod
    def is_external(self) -> bool: ...

    @property
    @abstractmethod
    def is_executable(self) -> bool: ...

    @property
    @abstractmethod
    def metadata(self) -> ArbitraryMetadataMapping: ...

    @property
    @abstractmethod
    def tags(self) -> Mapping[str, str]: ...

    @property
    @abstractmethod
    def pools(self) -> Optional[set[str]]: ...

    @property
    @abstractmethod
    def owners(self) -> Sequence[str]: ...

    @property
    @abstractmethod
    def is_partitioned(self) -> bool: ...

    @property
    @abstractmethod
    def legacy_freshness_policy(self) -> Optional[LegacyFreshnessPolicy]: ...

    @property
    @abstractmethod
    def freshness_policy(self) -> Optional[InternalFreshnessPolicy]:
        """WARNING: This field is not backwards compatible for policies created prior to 1.11.0.
        For backwards compatibility, use freshness_policy_or_from_metadata instead.
        """
        ...

    @property
    def freshness_policy_or_from_metadata(self) -> Optional[InternalFreshnessPolicy]:
        """Prior to 1.11.0, freshness policy was stored in the node metadata. Freshness policy is a first-class attribute of the asset starting in 1.11.0.

        This field is backwards compatible since it checks for the policy in both the top-level attribute and the node metadata.
        """
        from dagster._core.definitions.freshness import InternalFreshnessPolicy

        return self.freshness_policy or InternalFreshnessPolicy.from_asset_spec_metadata(
            self.metadata
        )

    @property
    @abstractmethod
    def auto_materialize_policy(self) -> Optional["AutoMaterializePolicy"]: ...

    @property
    @abstractmethod
    def auto_observe_interval_minutes(self) -> Optional[float]: ...

    @property
    @abstractmethod
    def backfill_policy(self) -> Optional[BackfillPolicy]: ...

    @property
    @abstractmethod
    def code_version(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def check_keys(self) -> AbstractSet[AssetCheckKey]: ...

    @property
    @abstractmethod
    def execution_set_asset_keys(self) -> AbstractSet[AssetKey]: ...

    @property
    @abstractmethod
    def execution_set_entity_keys(
        self,
    ) -> AbstractSet[Union[AssetKey, AssetCheckKey]]: ...

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<{self.key.to_user_string()}>"


class AssetCheckNode(BaseEntityNode[AssetCheckKey]):
    def __init__(
        self,
        key: AssetCheckKey,
        additional_deps: Sequence[AssetKey],
        blocking: bool,
        description: Optional[str],
        automation_condition: Optional["AutomationCondition[AssetCheckKey]"],
        metadata: ArbitraryMetadataMapping,
    ):
        self.key = key
        self.blocking = blocking
        self._automation_condition = automation_condition
        self._additional_deps = additional_deps
        self._description = description
        self._metadata = metadata

    @property
    def parent_entity_keys(self) -> AbstractSet[AssetKey]:
        return {self.key.asset_key, *self._additional_deps}

    @property
    def child_entity_keys(self) -> AbstractSet[EntityKey]:
        return {self.key.asset_key}

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        # all checks are unpartitioned
        return None

    @property
    def partition_mappings(self) -> Mapping[EntityKey, PartitionMapping]:
        return {}

    @property
    def automation_condition(self) -> Optional["AutomationCondition[AssetCheckKey]"]:
        return self._automation_condition

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self._metadata


T_AssetNode = TypeVar("T_AssetNode", bound=BaseAssetNode)


class BaseAssetGraph(ABC, Generic[T_AssetNode]):
    _asset_nodes_by_key: Mapping[AssetKey, T_AssetNode]
    _asset_check_nodes_by_key: Mapping[AssetCheckKey, AssetCheckNode]

    @property
    def asset_nodes(self) -> Iterable[T_AssetNode]:
        return self._asset_nodes_by_key.values()

    @property
    def nodes(self) -> Iterable[BaseEntityNode]:
        return [
            *self._asset_nodes_by_key.values(),
            *self._asset_check_nodes_by_key.values(),
        ]

    def has(self, key: EntityKey) -> bool:
        return key in self._asset_nodes_by_key or key in self._asset_check_nodes_by_key

    @overload
    def get(self, key: AssetKey) -> T_AssetNode: ...

    @overload
    def get(self, key: AssetCheckKey) -> AssetCheckNode: ...

    def get(self, key: EntityKey) -> Union[T_AssetNode, AssetCheckNode]:
        if isinstance(key, AssetKey):
            return self._asset_nodes_by_key[key]
        else:
            return self._asset_check_nodes_by_key[key]

    @cached_property
    def asset_dep_graph(self) -> DependencyGraph[AssetKey]:
        return {
            "upstream": {node.key: node.parent_keys for node in self.asset_nodes},
            "downstream": {node.key: node.child_keys for node in self.asset_nodes},
        }

    @cached_property
    def entity_dep_graph(self) -> DependencyGraph[EntityKey]:
        return {
            "upstream": {node.key: node.parent_entity_keys for node in self.nodes},
            "downstream": {node.key: node.child_entity_keys for node in self.nodes},
        }

    def get_all_asset_keys(self) -> AbstractSet[AssetKey]:
        return set(self._asset_nodes_by_key)

    # since this is an ABC and @cached_property has class level locking on py < 3.12
    # use property & cached_method instead

    @property
    @cached_method
    def materializable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for key, node in self._asset_nodes_by_key.items() if node.is_materializable}

    @property
    @cached_method
    def observable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for key, node in self._asset_nodes_by_key.items() if node.is_observable}

    @property
    @cached_method
    def external_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for key, node in self._asset_nodes_by_key.items() if node.is_external}

    @property
    @cached_method
    def executable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for key, node in self._asset_nodes_by_key.items() if node.is_executable}

    @property
    @cached_method
    def unexecutable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for key, node in self._asset_nodes_by_key.items() if not node.is_executable}

    @cached_property
    def toposorted_asset_keys(self) -> Sequence[AssetKey]:
        """Return topologically sorted asset keys in graph. Keys with the same topological level are
        sorted alphabetically to provide stability.
        """
        return [
            item
            for items_in_level in toposort(self.asset_dep_graph["upstream"])
            for item in sorted(items_in_level)
        ]

    @cached_property
    def toposorted_entity_keys_by_level(self) -> Sequence[Sequence[EntityKey]]:
        """Return topologically sorted levels for entity keys in graph. Keys with the same topological level are
        sorted alphabetically to provide stability.
        """
        sort_key = lambda e: (e, None) if isinstance(e, AssetKey) else (e.asset_key, e.name)
        return toposort(self.entity_dep_graph["upstream"], sort_key=sort_key)

    @cached_property
    def toposorted_asset_keys_by_level(self) -> Sequence[AbstractSet[AssetKey]]:
        """Return topologically sorted asset keys grouped into sets containing keys of the same
        topological level.
        """
        return [set(level) for level in toposort(self.asset_dep_graph["upstream"])]

    @cached_property
    def unpartitioned_asset_keys(self) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if not node.is_partitioned}

    def asset_keys_for_group(self, group_name: str) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if node.group_name == group_name}

    @cached_method
    def asset_keys_for_partitions_def(
        self, partitions_def: PartitionsDefinition
    ) -> AbstractSet[AssetKey]:
        return {node.key for node in self.asset_nodes if node.partitions_def == partitions_def}

    @cached_property
    def root_materializable_asset_keys(self) -> AbstractSet[AssetKey]:
        """Materializable asset keys that have no materializable parents."""
        from dagster._core.definitions.asset_selection import KeysAssetSelection

        return (
            KeysAssetSelection(selected_keys=list(self.materializable_asset_keys))
            .roots()
            .resolve(self)
        )

    @cached_property
    def root_executable_asset_keys(self) -> AbstractSet[AssetKey]:
        """Executable asset keys that have no executable parents."""
        return fetch_sources(
            self,
            self.observable_asset_keys | self.materializable_asset_keys,
        )

    @property
    @abstractmethod
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]: ...

    def get_check_keys_for_assets(
        self, asset_keys: AbstractSet[AssetKey]
    ) -> AbstractSet[AssetCheckKey]:
        return {
            asset_check_key
            for asset_check_key in self.asset_check_keys
            if asset_check_key.asset_key in asset_keys
        }

    @cached_property
    def all_partitions_defs(self) -> Sequence[PartitionsDefinition]:
        return sorted(
            set(node.partitions_def for node in self.asset_nodes if node.partitions_def),
            key=repr,
        )

    @cached_property
    def all_group_names(self) -> AbstractSet[str]:
        return {a.group_name for a in self.asset_nodes if a.group_name is not None}

    def get_partition_mapping(
        self, key: T_EntityKey, parent_asset_key: EntityKey
    ) -> PartitionMapping:
        node = self.get(key)
        return infer_partition_mapping(
            node.partition_mappings.get(parent_asset_key),
            node.partitions_def,
            self.get(parent_asset_key).partitions_def,
        )

    def get_children(self, node: T_AssetNode) -> AbstractSet[T_AssetNode]:
        """Returns all asset nodes that directly depend on the given asset node."""
        return {self._asset_nodes_by_key[key] for key in self.get(node.key).child_keys}

    def get_parents(self, node: T_AssetNode) -> AbstractSet[T_AssetNode]:
        """Returns all asset nodes that are direct dependencies on the given asset node."""
        return {self._asset_nodes_by_key[key] for key in self.get(node.key).parent_keys}

    def get_ancestor_asset_keys(
        self, asset_key: AssetKey, include_self: bool = False
    ) -> AbstractSet[AssetKey]:
        """Returns all nth-order dependencies of an asset."""
        ancestors = set()
        next_parents = self.get(asset_key).parent_keys - {asset_key}  # remove self-dependencies
        while next_parents:
            pending_next_parents = set()
            for node_key in next_parents:
                if node_key in ancestors:
                    continue
                ancestors.add(node_key)
                pending_next_parents.update(self.get(node_key).parent_keys)

            next_parents = pending_next_parents

        if include_self:
            ancestors.add(asset_key)
        return ancestors

    def get_partitions_in_range(
        self,
        asset_key: AssetKey,
        partition_key_range: PartitionKeyRange,
        dynamic_partitions_store: DynamicPartitionsStore,
    ) -> Sequence[AssetKeyPartitionKey]:
        partition_def = self.get(asset_key).partitions_def
        partition_keys_in_range = check.not_none(partition_def).get_partition_keys_in_range(
            partition_key_range, dynamic_partitions_store
        )
        return [
            AssetKeyPartitionKey(asset_key, partition_key)
            for partition_key in partition_keys_in_range
        ]

    def get_children_partitions(
        self,
        dynamic_partitions_store: DynamicPartitionsStore,
        current_time: datetime,
        asset_key: AssetKey,
        partition_key: Optional[str] = None,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns every partition in every of the given asset's children that depends on the given
        partition of that asset.
        """
        result: set[AssetKeyPartitionKey] = set()
        for child in self.get_children(self.get(asset_key)):
            if child.is_partitioned:
                for child_partition_key in self.get_child_partition_keys_of_parent(
                    dynamic_partitions_store,
                    partition_key,
                    asset_key,
                    child.key,
                    current_time,
                ):
                    result.add(AssetKeyPartitionKey(child.key, child_partition_key))
            else:
                result.add(AssetKeyPartitionKey(child.key))
        return result

    def get_child_partition_keys_of_parent(
        self,
        dynamic_partitions_store: DynamicPartitionsStore,
        parent_partition_key: Optional[str],
        parent_asset_key: AssetKey,
        child_asset_key: AssetKey,
        current_time: datetime,
    ) -> Sequence[str]:
        """Converts a partition key from one asset to the corresponding partition keys in a downstream
        asset. Uses the existing partition mapping between the child asset and the parent asset.

        Args:
            parent_partition_key (Optional[str]): The partition key to convert.
            parent_asset_key (AssetKey): The asset key of the upstream asset, which the provided
                partition key belongs to.
            child_asset_key (AssetKey): The asset key of the downstream asset. The provided partition
                key will be mapped to partitions within this asset.

        Returns:
            Sequence[str]: A list of the corresponding downstream partitions in child_asset_key that
                partition_key maps to.
        """
        child_partitions_def = self.get(child_asset_key).partitions_def
        parent_partitions_def = self.get(parent_asset_key).partitions_def

        if child_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Asset key {child_asset_key} is not partitioned. Cannot get partition keys."
            )
        if parent_partition_key is None:
            return child_partitions_def.get_partition_keys(
                dynamic_partitions_store=dynamic_partitions_store,
                current_time=current_time,
            )

        if parent_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Parent partition key '{parent_partition_key}' provided, but parent asset"
                f" '{parent_asset_key}' is not partitioned."
            )

        partition_mapping = self.get_partition_mapping(child_asset_key, parent_asset_key)
        child_partitions_subset = partition_mapping.get_downstream_partitions_for_partitions(
            parent_partitions_def.empty_subset().with_partition_keys([parent_partition_key]),
            parent_partitions_def,
            downstream_partitions_def=child_partitions_def,
            dynamic_partitions_store=dynamic_partitions_store,
            current_time=current_time,
        )

        return list(child_partitions_subset.get_partition_keys())

    def get_parents_partitions(
        self,
        dynamic_partitions_store: DynamicPartitionsStore,
        current_time: datetime,
        asset_key: AssetKey,
        partition_key: Optional[str] = None,
    ) -> ParentsPartitionsResult:
        """Returns every partition in every of the given asset's parents that the given partition of
        that asset depends on.
        """
        valid_parent_partitions: set[AssetKeyPartitionKey] = set()
        required_but_nonexistent_parent_partitions: set[AssetKeyPartitionKey] = set()
        for parent_asset_key in self.get(asset_key).parent_keys:
            if self.has(parent_asset_key) and self.get(parent_asset_key).is_partitioned:
                mapped_partitions_result = self.get_parent_partition_keys_for_child(
                    partition_key,
                    parent_asset_key,
                    asset_key,
                    dynamic_partitions_store=dynamic_partitions_store,
                    current_time=current_time,
                )

                valid_parent_partitions.update(
                    {
                        AssetKeyPartitionKey(parent_asset_key, valid_partition)
                        for valid_partition in mapped_partitions_result.partitions_subset.get_partition_keys()
                    }
                )
                required_but_nonexistent_parent_partitions.update(
                    {
                        AssetKeyPartitionKey(parent_asset_key, invalid_partition)
                        for invalid_partition in mapped_partitions_result.required_but_nonexistent_subset.get_partition_keys()
                    }
                )
            else:
                valid_parent_partitions.add(AssetKeyPartitionKey(parent_asset_key))

        return ParentsPartitionsResult(
            valid_parent_partitions, required_but_nonexistent_parent_partitions
        )

    def get_parent_partition_keys_for_child(
        self,
        partition_key: Optional[str],
        parent_asset_key: AssetKey,
        child_asset_key: AssetKey,
        dynamic_partitions_store: DynamicPartitionsStore,
        current_time: datetime,
    ) -> UpstreamPartitionsResult:
        """Converts a partition key from one asset to the corresponding partition keys in one of its
        parent assets. Uses the existing partition mapping between the child asset and the parent
        asset.

        Args:
            partition_key (Optional[str]): The partition key to convert.
            child_asset_key (AssetKey): The asset key of the child asset, which the provided
                partition key belongs to.
            parent_asset_key (AssetKey): The asset key of the parent asset. The provided partition
                key will be mapped to partitions within this asset.

        Returns:
            Sequence[str]: A list of the corresponding downstream partitions in child_asset_key that
                partition_key maps to.
        """
        partition_key = check.opt_str_param(partition_key, "partition_key")

        child_partitions_def = cast(
            "PartitionsDefinition", self.get(child_asset_key).partitions_def
        )
        parent_partitions_def = self.get(parent_asset_key).partitions_def

        if parent_partitions_def is None:
            raise DagsterInvalidInvocationError(
                f"Asset key {parent_asset_key} is not partitioned. Cannot get partition keys."
            )

        partition_mapping = self.get_partition_mapping(child_asset_key, parent_asset_key)

        return partition_mapping.get_upstream_mapped_partitions_result_for_partitions(
            (
                child_partitions_def.subset_with_partition_keys([partition_key])
                if partition_key
                else None
            ),
            downstream_partitions_def=child_partitions_def,
            upstream_partitions_def=parent_partitions_def,
            dynamic_partitions_store=dynamic_partitions_store,
            current_time=current_time,
        )

    def has_materializable_parents(self, asset_key: AssetKey) -> bool:
        """Determines if an asset has any parents which are materializable."""
        if self.get(asset_key).is_external:
            return False
        return any(
            self.has(parent_key) and self.get(parent_key).is_materializable
            for parent_key in self.get(asset_key).parent_keys - {asset_key}
        )

    def get_materializable_roots(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        """Returns all assets upstream of the given asset which do not consume any other
        materializable assets.
        """
        if not self.has_materializable_parents(asset_key):
            return {asset_key}
        return {
            key
            for key in self.upstream_key_iterator(asset_key)
            if self.has(key)
            and self.get(key).is_materializable
            and not self.has_materializable_parents(key)
        }

    def validate_partition_mappings(self):
        for node in self.asset_nodes:
            if node.is_external:
                continue

            parents = self.get_parents(node)
            for parent in parents:
                if parent.partitions_def is None or parent.is_external:
                    continue

                partition_mapping = self.get_partition_mapping(node.key, parent.key)

                try:
                    partition_mapping.validate_partition_mapping(
                        parent.partitions_def,
                        node.partitions_def,
                    )
                except Exception as e:
                    raise DagsterInvalidDefinitionError(
                        f"Invalid partition mapping from {node.key.to_user_string()} to {parent.key.to_user_string()}"
                    ) from e

    def upstream_key_iterator(self, asset_key: AssetKey) -> Iterator[AssetKey]:
        """Iterates through all asset keys which are upstream of the given key."""
        visited: set[AssetKey] = set()
        queue = deque([asset_key])
        while queue:
            current_key = queue.popleft()
            for parent_key in self.get(current_key).parent_keys:
                if parent_key not in visited:
                    yield parent_key
                    queue.append(parent_key)
                    visited.add(parent_key)

    @abstractmethod
    def get_execution_set_asset_and_check_keys(
        self, asset_key_or_check_key: EntityKey
    ) -> AbstractSet[EntityKey]:
        """For a given asset/check key, return the set of asset/check keys that must be
        materialized/computed at the same time.
        """
        ...

    @cached_method
    def get_downstream_legacy_freshness_policies(
        self, *, asset_key: AssetKey
    ) -> AbstractSet[LegacyFreshnessPolicy]:
        asset = self.get(asset_key)
        downstream_policies = set().union(
            *(
                self.get_downstream_legacy_freshness_policies(asset_key=child_key)
                for child_key in self.get(asset_key).child_keys
                if child_key != asset_key
            )
        )
        if asset.partitions_def is None and asset.legacy_freshness_policy is not None:
            downstream_policies.add(asset.legacy_freshness_policy)

        return downstream_policies

    @cached_method
    def get_downstream_automation_conditions(
        self, *, asset_key: AssetKey
    ) -> Mapping["AutomationCondition", AbstractSet[AssetKey]]:
        asset = self.get(asset_key)
        downstream_conditions = defaultdict(set)
        for child_key in asset.child_keys:
            child_policy = self.get(child_key).auto_materialize_policy
            child_condition = child_policy.asset_condition if child_policy else None
            if child_condition:
                downstream_conditions[child_condition].add(child_key)
            for c, aks in self.get_downstream_automation_conditions(asset_key=child_key).items():
                downstream_conditions[c].update(aks)
        return downstream_conditions

    def bfs_filter_subsets(
        self,
        dynamic_partitions_store: DynamicPartitionsStore,
        condition_fn: Callable[[AssetKey, Optional[PartitionsSubset]], bool],
        initial_subset: "AssetGraphSubset",
        current_time: datetime,
    ) -> "AssetGraphSubset":
        """Returns asset partitions within the graph that satisfy supplied criteria.

        - Are >= initial_asset_partitions
        - Asset matches the condition_fn
        - Any of their ancestors >= initial_asset_partitions match the condition_fn.

        Visits parents before children.
        """
        from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset

        all_assets = set(initial_subset.asset_keys)
        check.invariant(
            len(initial_subset.asset_keys) == 1,
            "Multiple initial assets not yet supported",
        )
        initial_asset_key = next(iter(initial_subset.asset_keys))
        queue = deque([initial_asset_key])

        queued_subsets_by_asset_key: dict[AssetKey, Optional[PartitionsSubset]] = {
            initial_asset_key: (
                initial_subset.get_partitions_subset(initial_asset_key, self)
                if self.get(initial_asset_key).is_partitioned
                else None
            ),
        }
        result = AssetGraphSubset()

        while len(queue) > 0:
            asset_key = queue.popleft()
            partitions_subset = queued_subsets_by_asset_key.get(asset_key)

            if condition_fn(asset_key, partitions_subset):
                result |= AssetGraphSubset(
                    non_partitioned_asset_keys={asset_key} if partitions_subset is None else set(),
                    partitions_subsets_by_asset_key=(
                        {asset_key: partitions_subset} if partitions_subset is not None else {}
                    ),
                )

                for child_key in self.get(asset_key).child_keys:
                    partition_mapping = self.get_partition_mapping(child_key, asset_key)
                    child_partitions_def = self.get(child_key).partitions_def

                    if child_partitions_def:
                        if partitions_subset is None:
                            child_partitions_subset = (
                                child_partitions_def.subset_with_all_partitions(
                                    current_time=current_time,
                                    dynamic_partitions_store=dynamic_partitions_store,
                                )
                            )
                            queued_subsets_by_asset_key[child_key] = child_partitions_subset
                        else:
                            child_partitions_subset = (
                                partition_mapping.get_downstream_partitions_for_partitions(
                                    partitions_subset,
                                    check.not_none(self.get(asset_key).partitions_def),
                                    downstream_partitions_def=child_partitions_def,
                                    dynamic_partitions_store=dynamic_partitions_store,
                                    current_time=current_time,
                                )
                            )
                            prior_child_partitions_subset = queued_subsets_by_asset_key.get(
                                child_key
                            )
                            queued_subsets_by_asset_key[child_key] = (
                                child_partitions_subset
                                if not prior_child_partitions_subset
                                else child_partitions_subset | prior_child_partitions_subset
                            )
                    else:
                        child_partitions_subset = None

                    if child_key not in all_assets:
                        queue.append(child_key)
                        all_assets.add(child_key)

        return result

    def split_entity_keys_by_repository(
        self, keys: AbstractSet[EntityKey]
    ) -> Sequence[AbstractSet[EntityKey]]:
        return [keys]

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        return self is other


def sort_key_for_asset_partition(
    asset_graph: BaseAssetGraph, asset_partition: AssetKeyPartitionKey
) -> float:
    """Returns an integer sort key such that asset partitions are sorted in the order in which they
    should be materialized. For assets without a time window partition dimension, this is always 0.
    Assets with a time window partition dimension will be sorted from newest to oldest, unless they
    have a self-dependency, in which case they are sorted from oldest to newest.
    """
    partitions_def = asset_graph.get(asset_partition.asset_key).partitions_def
    time_partitions_def = get_time_partitions_def(partitions_def)
    if time_partitions_def is None:
        return 0

    # A sort key such that time window partitions are sorted from oldest to newest
    time_partition_key = get_time_partition_key(partitions_def, asset_partition.partition_key)
    partition_timestamp = time_partitions_def.start_time_for_partition_key(
        time_partition_key
    ).timestamp()

    if asset_graph.get(asset_partition.asset_key).has_self_dependency:
        # sort self dependencies from oldest to newest, as older partitions must exist before
        # new ones can execute
        return partition_timestamp
    else:
        # sort non-self dependencies from newest to oldest, as newer partitions are more relevant
        # than older ones
        return -1 * partition_timestamp
