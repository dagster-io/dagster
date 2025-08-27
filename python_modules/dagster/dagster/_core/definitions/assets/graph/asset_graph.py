from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from functools import cached_property
from typing import AbstractSet, Optional, Union  # noqa: UP035

from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.assets.graph.base_asset_graph import (
    AssetCheckNode,
    BaseAssetGraph,
    BaseAssetNode,
    EntityKey,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping import PartitionMapping
from dagster._core.definitions.resolved_asset_deps import ResolvedAssetDependencies
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.selector.subset_selector import generate_asset_dep_graph
from dagster._utils.warnings import disable_dagster_warnings


class AssetNode(BaseAssetNode):
    def __init__(
        self,
        key: AssetKey,
        parent_keys: AbstractSet[AssetKey],
        child_keys: AbstractSet[AssetKey],
        assets_def: AssetsDefinition,
        check_keys: AbstractSet[AssetCheckKey],
    ):
        self.key = key
        self.parent_keys = parent_keys
        self.child_keys = child_keys
        self.assets_def = assets_def
        self._check_keys = check_keys
        self._spec = assets_def.specs_by_key[key]

    @property
    def description(self) -> Optional[str]:
        return self._spec.description

    @property
    def group_name(self) -> str:
        return self._spec.group_name or DEFAULT_GROUP_NAME

    @property
    def is_materializable(self) -> bool:
        return self.assets_def.is_materializable

    @property
    def is_observable(self) -> bool:
        return self.assets_def.is_observable

    @property
    def is_external(self) -> bool:
        return self.assets_def.is_external

    @property
    def is_executable(self) -> bool:
        return self.assets_def.is_executable

    @property
    def metadata(self) -> ArbitraryMetadataMapping:
        return self._spec.metadata

    @property
    def tags(self) -> Mapping[str, str]:
        return self._spec.tags

    @property
    def kinds(self) -> AbstractSet[str]:
        return self._spec.kinds or set()

    @property
    def pools(self) -> Optional[set[str]]:
        if not self.assets_def.computation:
            return None
        return set(
            op_def.pool
            for op_def in self.assets_def.computation.node_def.iterate_op_defs()
            if op_def.pool
        )

    @property
    def owners(self) -> Sequence[str]:
        return self._spec.owners

    @property
    def is_partitioned(self) -> bool:
        return self.partitions_def is not None

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.assets_def.specs_by_key[self.key].partitions_def

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._spec.partition_mappings

    @property
    def legacy_freshness_policy(self) -> Optional[LegacyFreshnessPolicy]:
        return self._spec.legacy_freshness_policy

    @property
    def freshness_policy(self) -> Optional[InternalFreshnessPolicy]:
        return self._spec.freshness_policy

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self._spec.auto_materialize_policy

    @property
    def automation_condition(self) -> Optional[AutomationCondition]:
        return self._spec.automation_condition

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return self.assets_def.auto_observe_interval_minutes

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self.assets_def.backfill_policy

    @property
    def code_version(self) -> Optional[str]:
        return self._spec.code_version

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self._check_keys

    @property
    def execution_set_asset_keys(self) -> AbstractSet[AssetKey]:
        return (
            {self.key}
            if len(self.assets_def.keys) <= 1 or self.assets_def.can_subset
            else self.assets_def.keys
        )

    @property
    def execution_set_entity_keys(self) -> AbstractSet[EntityKey]:
        if self.assets_def.can_subset:
            return {self.key}
        else:
            return self.assets_def.asset_and_check_keys

    ##### ASSET GRAPH SPECIFIC INTERFACE

    @property
    def execution_type(self) -> AssetExecutionType:
        return self.assets_def.execution_type

    @property
    def io_manager_key(self) -> str:
        return self.assets_def.get_io_manager_key_for_asset_key(self.key)

    def to_asset_spec(self) -> AssetSpec:
        return self._spec


class AssetGraph(BaseAssetGraph[AssetNode]):
    _assets_defs_by_check_key: Mapping[AssetCheckKey, AssetsDefinition]

    def __init__(
        self,
        asset_nodes_by_key: Mapping[AssetKey, AssetNode],
        assets_defs_by_check_key: Mapping[AssetCheckKey, AssetsDefinition],
    ):
        self._asset_nodes_by_key = asset_nodes_by_key
        self._asset_check_nodes_by_key = {
            k: AssetCheckNode(
                k,
                [d.asset_key for d in v.get_spec_for_check_key(k).additional_deps],
                v.get_spec_for_check_key(k).blocking,
                v.get_spec_for_check_key(k).description,
                v.get_spec_for_check_key(k).automation_condition,
                v.get_spec_for_check_key(k).metadata,
            )
            for k, v in assets_defs_by_check_key.items()
        }
        self._assets_defs_by_check_key = assets_defs_by_check_key

    @staticmethod
    def normalize_assets(
        assets: Iterable[Union[AssetsDefinition, SourceAsset]],
    ) -> Sequence[AssetsDefinition]:
        """Normalize a mixed list of AssetsDefinition and SourceAsset to a list of AssetsDefinition.

        Normalization includse:

        - Converting any SourceAsset to an AssetDefinition
        - Resolving all relative asset keys (that sometimes specify dependencies) to absolute asset
          keys
        - Creating unexecutable external asset definitions for any keys referenced by asset checks
          or as dependencies, but for which no definition was provided.
        """
        from dagster._core.definitions.external_asset import create_external_asset_from_source_asset

        # Convert any source assets to external assets
        assets_defs = [
            create_external_asset_from_source_asset(a) if isinstance(a, SourceAsset) else a
            for a in assets
        ]
        all_keys = {k for asset_def in assets_defs for k in asset_def.keys}

        # Resolve all asset dependencies. An asset dependency is resolved when its key is an
        # AssetKey not subject to any further manipulation.
        resolved_deps = ResolvedAssetDependencies(assets_defs, [])

        asset_key_replacements = [
            {
                raw_key: normalized_key
                for input_name, raw_key in ad.keys_by_input_name.items()
                if (
                    normalized_key := resolved_deps.get_resolved_asset_key_for_input(ad, input_name)
                )
                != raw_key
            }
            for ad in assets_defs
        ]

        # Only update the assets defs if we're actually replacing input asset keys
        assets_defs = [
            ad.with_attributes(asset_key_replacements=reps) if reps else ad
            for ad, reps in zip(assets_defs, asset_key_replacements)
        ]

        # Create unexecutable external assets definitions for any referenced keys for which no
        # definition was provided.
        all_referenced_asset_keys = {
            key for assets_def in assets_defs for key in assets_def.dependency_keys
        }.union(
            {
                check_spec.key.asset_key
                for assets_def in assets_defs
                for check_spec in assets_def.node_check_specs_by_output_name.values()
            }
        )

        with disable_dagster_warnings():
            for key in all_referenced_asset_keys.difference(all_keys):
                assets_defs.append(
                    AssetsDefinition(
                        specs=[
                            AssetSpec(
                                key=key,
                                metadata={SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET: True},
                            )
                        ]
                    )
                )
        return assets_defs

    @classmethod
    def key_mappings_from_assets(
        cls,
        assets: Iterable[Union[AssetsDefinition, SourceAsset]],
    ) -> tuple[Mapping[AssetKey, AssetNode], Mapping[AssetCheckKey, AssetsDefinition]]:
        assets_defs = cls.normalize_assets(assets)

        # Build the set of AssetNodes. Each node holds key rather than object references to parent
        # and child nodes.
        dep_graph = generate_asset_dep_graph(assets_defs)

        assets_defs_by_check_key: dict[AssetCheckKey, AssetsDefinition] = {}
        check_keys_by_asset_key: defaultdict[AssetKey, set[AssetCheckKey]] = defaultdict(set)
        for ad in assets_defs:
            for ck in ad.check_keys:
                check_keys_by_asset_key[ck.asset_key].add(ck)
                assets_defs_by_check_key[ck] = ad

        asset_nodes_by_key = {
            key: AssetNode(
                key=key,
                parent_keys=dep_graph["upstream"][key],
                child_keys=dep_graph["downstream"][key],
                assets_def=ad,
                check_keys=check_keys_by_asset_key[key],
            )
            for ad in assets_defs
            for key in ad.keys
        }

        return (asset_nodes_by_key, assets_defs_by_check_key)

    @classmethod
    def from_assets(
        cls,
        assets: Iterable[Union[AssetsDefinition, SourceAsset]],
    ) -> "AssetGraph":
        asset_nodes_by_key, assets_defs_by_check_key = cls.key_mappings_from_assets(assets)
        return AssetGraph(
            asset_nodes_by_key=asset_nodes_by_key,
            assets_defs_by_check_key=assets_defs_by_check_key,
        )

    def get_execution_set_asset_and_check_keys(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, entity_key: EntityKey
    ) -> AbstractSet[EntityKey]:
        if isinstance(entity_key, AssetKey):
            return self.get(entity_key).execution_set_entity_keys
        else:  # AssetCheckKey
            assets_def = self._assets_defs_by_check_key[entity_key]
            return {entity_key} if assets_def.can_subset else assets_def.asset_and_check_keys

    def get_execution_set_identifier(self, entity_key: EntityKey) -> Optional[str]:
        """All assets and asset checks with the same execution_set_identifier must be executed
        together - i.e. you can't execute just a subset of them.

        Returns None if the asset or asset check can be executed individually.
        """
        from dagster._core.definitions.graph_definition import GraphDefinition

        if isinstance(entity_key, AssetKey):
            assets_def = self.get(entity_key).assets_def
            return (
                assets_def.unique_id
                if (
                    assets_def.is_executable
                    and not assets_def.can_subset
                    and (len(assets_def.keys) > 1 or assets_def.check_keys)
                )
                else None
            )

        else:  # AssetCheckKey
            assets_def = self._assets_defs_by_check_key[entity_key]
            # Executing individual checks isn't supported in graph assets
            if isinstance(assets_def.node_def, GraphDefinition):
                return assets_def.unique_id
            else:
                return assets_def.unique_id if not assets_def.can_subset else None

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return list(
            {
                *(asset.assets_def for asset in self.asset_nodes),
                *(ad for ad in self._assets_defs_by_check_key.values()),
            }
        )

    def assets_defs_for_keys(self, keys: Iterable[EntityKey]) -> Sequence[AssetsDefinition]:
        return list({self.assets_def_for_key(key) for key in keys})

    def assets_def_for_key(self, key: EntityKey) -> AssetsDefinition:
        if isinstance(key, AssetKey):
            return self.get(key).assets_def
        else:
            return self._assets_defs_by_check_key[key]

    @cached_property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return {key for ad in self.assets_defs for key in ad.check_keys}

    @cached_property
    def unpartitioned_assets_def_asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        """Asset check keys that correspond to unpartitioned AssetsDefinitions."""
        return {
            k for k in self.asset_check_keys if self.assets_def_for_key(k).partitions_def is None
        }

    def get_check_spec(self, key: AssetCheckKey) -> AssetCheckSpec:
        return self._assets_defs_by_check_key[key].get_spec_for_check_key(key)

    @property
    def source_asset_graph(self) -> "AssetGraph":
        return self


def executable_in_same_run(
    asset_graph: BaseAssetGraph, child_key: EntityKey, parent_key: EntityKey
):
    """Returns whether a child asset can be materialized in the same run as a parent asset."""
    from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteWorkspaceAssetGraph
    from dagster._core.definitions.partitions.mapping import (
        IdentityPartitionMapping,
        TimeWindowPartitionMapping,
    )

    child_node = asset_graph.get(child_key)
    parent_node = asset_graph.get(parent_key)

    # if operating on a RemoteWorkspaceAssetGraph, must share a repository handle
    if isinstance(asset_graph, RemoteWorkspaceAssetGraph):
        child_handle = asset_graph.get_repository_handle(child_key)
        parent_handle = asset_graph.get_repository_handle(parent_key)
        if child_handle != parent_handle:
            return False

    # partitions definitions must match
    if child_node.partitions_def != parent_node.partitions_def:
        return False

    # unpartitioned assets can always execute together
    if child_node.partitions_def is None:
        return True

    return isinstance(
        asset_graph.get_partition_mapping(child_node.key, parent_node.key),
        (TimeWindowPartitionMapping, IdentityPartitionMapping),
    )
