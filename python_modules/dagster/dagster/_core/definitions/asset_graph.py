from collections import defaultdict
from functools import cached_property
from typing import AbstractSet, DefaultDict, Dict, Iterable, Mapping, Optional, Sequence, Set, Union

from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.assets import AssetsDefinition, asset_owner_to_str
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.base_asset_graph import (
    AssetKeyOrCheckKey,
    BaseAssetGraph,
    BaseAssetNode,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.resolved_asset_deps import ResolvedAssetDependencies
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.selector.subset_selector import (
    generate_asset_dep_graph,
)


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

    @property
    def description(self) -> Optional[str]:
        return self.assets_def.descriptions_by_key.get(self.key)

    @property
    def group_name(self) -> str:
        return self.assets_def.group_names_by_key.get(self.key, DEFAULT_GROUP_NAME)

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
        return self.assets_def.metadata_by_key.get(self.key, {})

    @property
    def tags(self) -> Mapping[str, str]:
        return self.assets_def.tags_by_key.get(self.key, {})

    @property
    def owners(self) -> Sequence[str]:
        return [
            asset_owner_to_str(owner) for owner in self.assets_def.owners_by_key.get(self.key, [])
        ]

    @property
    def is_partitioned(self) -> bool:
        return self.assets_def.partitions_def is not None

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self.assets_def.partitions_def

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        return self.assets_def.partition_mappings

    @property
    def freshness_policy(self) -> Optional[FreshnessPolicy]:
        return self.assets_def.freshness_policies_by_key.get(self.key)

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return self.assets_def.auto_materialize_policies_by_key.get(self.key)

    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        return self.assets_def.auto_observe_interval_minutes

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self.assets_def.backfill_policy

    @property
    def code_version(self) -> Optional[str]:
        return self.assets_def.code_versions_by_key.get(self.key)

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
    def execution_set_asset_and_check_keys(self) -> AbstractSet[AssetKeyOrCheckKey]:
        if self.assets_def.can_subset or (
            len(self.assets_def.keys) <= 1 and not len(self.assets_def.check_keys) > 0
        ):
            return {self.key}
        else:
            return {*self.assets_def.keys, *self.assets_def.check_keys}

    ##### ASSET GRAPH SPECIFIC INTERFACE

    @property
    def execution_type(self) -> AssetExecutionType:
        return self.assets_def.execution_type

    @property
    def io_manager_key(self) -> str:
        return self.assets_def.get_io_manager_key_for_asset_key(self.key)


class AssetGraph(BaseAssetGraph[AssetNode]):
    _assets_defs_by_check_key: Mapping[AssetCheckKey, AssetsDefinition]

    def __init__(
        self,
        asset_nodes_by_key: Mapping[AssetKey, AssetNode],
        assets_defs_by_check_key: Mapping[AssetCheckKey, AssetsDefinition],
    ):
        self._asset_nodes_by_key = asset_nodes_by_key
        self._assets_defs_by_check_key = assets_defs_by_check_key
        self._asset_nodes_by_check_key = {
            check_key: asset
            for asset in asset_nodes_by_key.values()
            for check_key in asset.check_keys
        }

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
        from dagster._core.definitions.external_asset import (
            create_external_asset_from_source_asset,
            external_asset_from_spec,
        )

        # Convert any source assets to external assets
        assets_defs = [
            create_external_asset_from_source_asset(a) if isinstance(a, SourceAsset) else a
            for a in assets
        ]
        all_keys = {k for asset_def in assets_defs for k in asset_def.keys}

        # Resolve all asset dependencies. An asset dependency is resolved when its key is an
        # AssetKey not subject to any further manipulation.
        resolved_deps = ResolvedAssetDependencies(assets_defs, [])
        assets_defs = [
            ad.with_attributes(
                input_asset_key_replacements={
                    raw_key: resolved_deps.get_resolved_asset_key_for_input(ad, input_name)
                    for input_name, raw_key in ad.keys_by_input_name.items()
                }
            )
            for ad in assets_defs
        ]

        # Create unexecutable external assets definitions for any referenced keys for which no
        # definition was provided.
        all_referenced_asset_keys = {
            key for assets_def in assets_defs for key in assets_def.dependency_keys
        }
        for key in all_referenced_asset_keys.difference(all_keys):
            assets_defs.append(
                external_asset_from_spec(
                    AssetSpec(key=key, metadata={SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET: True})
                )
            )
        return assets_defs

    @classmethod
    def from_assets(
        cls,
        assets: Iterable[Union[AssetsDefinition, SourceAsset]],
    ) -> "AssetGraph":
        assets_defs = cls.normalize_assets(assets)

        # Build the set of AssetNodes. Each node holds key rather than object references to parent
        # and child nodes.
        dep_graph = generate_asset_dep_graph(assets_defs)

        assets_defs_by_check_key: Dict[AssetCheckKey, AssetsDefinition] = {}
        check_keys_by_asset_key: DefaultDict[AssetKey, Set[AssetCheckKey]] = defaultdict(set)
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

        return AssetGraph(
            asset_nodes_by_key=asset_nodes_by_key,
            assets_defs_by_check_key=assets_defs_by_check_key,
        )

    def get_execution_set_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            return self.get(asset_or_check_key).execution_set_asset_and_check_keys
        else:  # AssetCheckKey
            asset_node = self._asset_nodes_by_check_key[asset_or_check_key]
            asset_unit_keys = asset_node.execution_set_asset_and_check_keys
            return (
                asset_unit_keys if asset_or_check_key in asset_unit_keys else {asset_or_check_key}
            )

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return list(
            {
                *(asset.assets_def for asset in self.asset_nodes),
                *(ad for ad in self._assets_defs_by_check_key.values()),
            }
        )

    def assets_defs_for_keys(
        self, keys: Iterable[AssetKeyOrCheckKey]
    ) -> Sequence[AssetsDefinition]:
        return list(
            {
                *[self.get(key).assets_def for key in keys if isinstance(key, AssetKey)],
                *[
                    self._assets_defs_by_check_key[key]
                    for key in keys
                    if isinstance(key, AssetCheckKey)
                ],
            }
        )

    @cached_property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return {key for ad in self.assets_defs for key in ad.check_keys}
