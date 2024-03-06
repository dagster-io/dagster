from typing import AbstractSet, Iterable, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    AssetSpec,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.base_asset_graph import AssetKeyOrCheckKey, BaseAssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.resolved_asset_deps import ResolvedAssetDependencies
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.selector.subset_selector import DependencyGraph, generate_asset_dep_graph
from dagster._utils.cached_method import cached_method


class AssetGraph(BaseAssetGraph):
    def __init__(
        self,
        assets_defs: Sequence[AssetsDefinition],
        asset_checks_defs: Sequence[AssetChecksDefinition],
    ):
        self._assets_defs = assets_defs
        self._assets_defs_by_key = {key: asset for asset in self._assets_defs for key in asset.keys}
        self._assets_defs_by_check_key = {
            **{check_key: asset for asset in assets_defs for check_key in asset.check_keys},
            **{
                check_key: self._assets_defs_by_key[check.asset_key]
                for check in asset_checks_defs
                for check_key in check.keys
                if check.asset_key in self._assets_defs_by_key
            },
        }

        self._asset_checks_defs = asset_checks_defs
        self._asset_checks_defs_by_key = {
            key: check for check in asset_checks_defs for key in check.keys
        }

    @staticmethod
    def normalize_assets(
        assets: Iterable[Union[AssetsDefinition, SourceAsset]],
        checks_defs: Optional[Iterable[AssetChecksDefinition]] = None,
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

        checks_defs = checks_defs or []

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
            *(key for asset_def in assets_defs for key in asset_def.dependency_keys),
            *(checks_def.asset_key for checks_def in checks_defs),
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
        all_assets: Iterable[Union[AssetsDefinition, SourceAsset]],
        asset_checks: Optional[Sequence[AssetChecksDefinition]] = None,
    ) -> "AssetGraph":
        assets_defs = cls.normalize_assets(all_assets)
        return AssetGraph(
            assets_defs=assets_defs,
            asset_checks_defs=asset_checks or [],
        )

    @property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return {
            *(key for check in self._asset_checks_defs for key in check.keys),
            *(key for asset in self._assets_defs for key in asset.check_keys),
        }

    @property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return self._assets_defs

    def get_assets_def(self, asset_key: AssetKey) -> AssetsDefinition:
        return self._assets_defs_by_key[asset_key]

    def has_asset(self, asset_key: AssetKey) -> bool:
        return asset_key in self._assets_defs_by_key

    def get_assets_def_for_check(
        self, asset_check_key: AssetCheckKey
    ) -> Optional[AssetsDefinition]:
        return self._assets_defs_by_check_key.get(asset_check_key)

    @property
    def asset_checks_defs(self) -> Sequence[AssetChecksDefinition]:
        return self._asset_checks_defs

    def get_asset_checks_def(self, asset_check_key: AssetCheckKey) -> AssetChecksDefinition:
        return self._asset_checks_defs_by_key[asset_check_key]

    def has_asset_check(self, asset_check_key: AssetCheckKey) -> bool:
        return asset_check_key in self._asset_checks_defs_by_key

    @property
    @cached_method
    def asset_dep_graph(self) -> DependencyGraph[AssetKey]:
        return generate_asset_dep_graph(self._assets_defs, [])

    @property
    @cached_method
    def all_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for ad in self._assets_defs for key in ad.keys}

    @property
    @cached_method
    def materializable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for ad in self._assets_defs if ad.is_materializable for key in ad.keys}

    def is_materializable(self, asset_key: AssetKey) -> bool:
        return self.get_assets_def(asset_key).is_materializable

    @property
    @cached_method
    def observable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for ad in self._assets_defs if ad.is_observable for key in ad.keys}

    def is_observable(self, asset_key: AssetKey) -> bool:
        return self.get_assets_def(asset_key).is_observable

    @property
    @cached_method
    def external_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for ad in self._assets_defs if ad.is_external for key in ad.keys}

    def is_external(self, asset_key: AssetKey) -> bool:
        return self.get_assets_def(asset_key).is_external

    @property
    @cached_method
    def executable_asset_keys(self) -> AbstractSet[AssetKey]:
        return {key for ad in self._assets_defs if ad.is_executable for key in ad.keys}

    def is_executable(self, asset_key: AssetKey) -> bool:
        return self.get_assets_def(asset_key).is_executable

    def asset_keys_for_group(self, group_name: str) -> AbstractSet[AssetKey]:
        return {
            key
            for ad in self._assets_defs
            for key in ad.keys
            if ad.group_names_by_key[key] == group_name
        }

    def get_execution_set_asset_keys(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        asset = self.get_assets_def(asset_key)
        return {asset_key} if len(asset.keys) <= 1 or asset.can_subset else asset.keys

    def get_execution_set_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            asset = self.get_assets_def(asset_or_check_key)
        else:  # AssetCheckKey
            # only checks emitted by AssetsDefinition have required keys
            if self.has_asset_check(asset_or_check_key):
                return {asset_or_check_key}
            else:
                asset = self.get_assets_def_for_check(asset_or_check_key)
                if asset is None or asset_or_check_key not in asset.check_keys:
                    return {asset_or_check_key}
        has_checks = len(asset.check_keys) > 0
        if asset.can_subset or len(asset.keys) <= 1 and not has_checks:
            return {asset_or_check_key}
        else:
            return {*asset.keys, *asset.check_keys}

    @property
    @cached_method
    def all_group_names(self) -> AbstractSet[str]:
        return {
            group_name for ad in self._assets_defs for group_name in ad.group_names_by_key.values()
        }

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        return self.get_assets_def(asset_key).partitions_def

    def get_partition_mappings(self, asset_key: AssetKey) -> Mapping[AssetKey, PartitionMapping]:
        return self.get_assets_def(asset_key).partition_mappings

    def get_group_name(self, asset_key: AssetKey) -> Optional[str]:
        return self.get_assets_def(asset_key).group_names_by_key.get(asset_key)

    def get_freshness_policy(self, asset_key: AssetKey) -> Optional[FreshnessPolicy]:
        return self.get_assets_def(asset_key).freshness_policies_by_key.get(asset_key)

    def get_auto_materialize_policy(self, asset_key: AssetKey) -> Optional[AutoMaterializePolicy]:
        return self.get_assets_def(asset_key).auto_materialize_policies_by_key.get(asset_key)

    def get_auto_observe_interval_minutes(self, asset_key: AssetKey) -> Optional[float]:
        return self.get_assets_def(asset_key).auto_observe_interval_minutes

    def get_backfill_policy(self, asset_key: AssetKey) -> Optional[BackfillPolicy]:
        return self.get_assets_def(asset_key).backfill_policy

    def get_code_version(self, asset_key: AssetKey) -> Optional[str]:
        return self.get_assets_def(asset_key).code_versions_by_key.get(asset_key)
