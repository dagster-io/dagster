from functools import cached_property
from typing import AbstractSet, Iterable, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_layer import subset_assets_defs
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.assets import AssetsDefinition
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
    _asset_check_defs_by_key: Mapping[AssetCheckKey, AssetsDefinition]

    def __init__(
        self,
        asset_nodes_by_key: Mapping[AssetKey, AssetNode],
        asset_check_defs_by_key: Mapping[AssetCheckKey, AssetsDefinition],
    ):
        self._asset_nodes_by_key = asset_nodes_by_key
        self._asset_check_defs_by_key = asset_check_defs_by_key
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
        asset_nodes_by_key = {
            key: AssetNode(
                key=key,
                parent_keys=dep_graph["upstream"][key],
                child_keys=dep_graph["downstream"][key],
                assets_def=ad,
                check_keys={
                    *(ck for ad in assets_defs for ck in ad.check_keys if ck.asset_key == key),
                },
            )
            for ad in assets_defs
            for key in ad.keys
        }

        asset_check_defs_by_key = {
            key: assets_def for assets_def in assets_defs for key in assets_def.check_keys
        }

        return AssetGraph(
            asset_nodes_by_key=asset_nodes_by_key,
            asset_check_defs_by_key=asset_check_defs_by_key,
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
                *(ad for ad in self._asset_check_defs_by_key.values()),
            }
        )

    def assets_defs_for_keys(
        self, keys: Iterable[AssetKeyOrCheckKey]
    ) -> Sequence[AssetsDefinition]:
        return list(
            {
                *[self.get(key).assets_def for key in keys if isinstance(key, AssetKey)],
                *[
                    ad
                    for k, ad in self._asset_check_defs_by_key.items()
                    if k in keys and isinstance(ad, AssetsDefinition)
                ],
            }
        )

    @cached_property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return {key for ad in self.assets_defs for key in ad.check_keys}

    def get_subset(
        self,
        executable_asset_keys: AbstractSet[AssetKey],
        asset_check_keys: Optional[AbstractSet[AssetCheckKey]] = None,
    ) -> "AssetGraph":
        """Returns a new asset graph where only the provided asset keys are executable. All parent
        keys of a selected executable asset will be included as unexecutable external assets (unless
        they are themselves present in the executable selection).
        """
        from dagster._core.definitions.external_asset import (
            create_unexecutable_external_assets_from_assets_def,
        )

        invalid_executable_keys = executable_asset_keys - self.executable_asset_keys
        if invalid_executable_keys:
            check.failed(
                "Provided executable asset keys must be a subset of existing executable asset keys."
                f" Invalid provided keys: {invalid_executable_keys}",
            )

        # subset_assets_defs returns two lists of Assetsfinitions-- those included and those
        # excluded by the selection. These collections retain their original execution type. We need
        # to convert the excluded assets to unexecutable external assets.
        executable_assets_defs, excluded_assets_defs = subset_assets_defs(
            self.assets_defs, executable_asset_keys, asset_check_keys
        )
        loadable_assets_defs = [
            unexecutable_ad
            for ad in excluded_assets_defs
            for unexecutable_ad in create_unexecutable_external_assets_from_assets_def(ad)
        ]

        return self.from_assets([*executable_assets_defs, *loadable_assets_defs])
