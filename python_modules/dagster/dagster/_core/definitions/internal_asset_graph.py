from typing import AbstractSet, Iterable, List, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_graph import AssetGraph, AssetKeyOrCheckKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.selector.subset_selector import DependencyGraph, generate_asset_dep_graph
from dagster._utils.cached_method import cached_method


class InternalAssetGraph(AssetGraph):
    def __init__(
        self,
        assets_defs: Sequence[AssetsDefinition],
        source_assets: Sequence[SourceAsset],
        asset_checks_defs: Sequence[AssetChecksDefinition],
    ):
        from dagster._core.definitions.external_asset import create_external_asset_from_source_asset

        self._assets_defs = [
            *assets_defs,
            *(create_external_asset_from_source_asset(sa) for sa in source_assets),
        ]
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
    def from_assets(
        all_assets: Iterable[Union[AssetsDefinition, SourceAsset]],
        asset_checks: Optional[Sequence[AssetChecksDefinition]] = None,
    ) -> "InternalAssetGraph":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph

        assets_defs: List[AssetsDefinition] = []
        source_assets: List[SourceAsset] = []
        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
            else:  # AssetsDefinition
                assets_defs.append(asset)
        return InternalAssetGraph(
            assets_defs=assets_defs,
            asset_checks_defs=asset_checks or [],
            source_assets=source_assets,
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

    def includes_materializable_and_external_assets(
        self, asset_keys: AbstractSet[AssetKey]
    ) -> bool:
        """Returns true if the given asset keys contains at least one materializable asset and
        at least one external asset.
        """
        selected_external_assets = self.external_asset_keys & asset_keys
        selected_materializable_assets = self.materializable_asset_keys & asset_keys
        return len(selected_external_assets) > 0 and len(selected_materializable_assets) > 0

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
        # Performing an existence check temporarily until we change callsites
        return self.has_asset(asset_key) and self.get_assets_def(asset_key).is_materializable

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
        # Performing an existence check temporarily until we change callsites
        return self.has_asset(asset_key) and self.get_assets_def(asset_key).is_executable

    def asset_keys_for_group(self, group_name: str) -> AbstractSet[AssetKey]:
        return {
            key
            for ad in self._assets_defs
            for key in ad.keys
            if ad.group_names_by_key[key] == group_name
        }

    def get_required_multi_asset_keys(self, asset_key: AssetKey) -> AbstractSet[AssetKey]:
        asset = self.get_assets_def(asset_key)
        return set() if len(asset.keys) <= 1 or asset.can_subset else asset.keys

    def get_required_asset_and_check_keys(
        self, asset_or_check_key: AssetKeyOrCheckKey
    ) -> AbstractSet[AssetKeyOrCheckKey]:
        if isinstance(asset_or_check_key, AssetKey):
            asset = self.get_assets_def(asset_or_check_key)
        else:  # AssetCheckKey
            # only checks emitted by AssetsDefinition have required keys
            if self.has_asset_check(asset_or_check_key):
                return set()
            else:
                asset = self.get_assets_def_for_check(asset_or_check_key)
                if asset is None or asset_or_check_key not in asset.check_keys:
                    return set()
        has_checks = len(asset.check_keys) > 0
        if asset.can_subset or len(asset.keys) <= 1 and not has_checks:
            return set()
        else:
            return {*asset.keys, *asset.check_keys}

    @property
    @cached_method
    def all_group_names(self) -> AbstractSet[str]:
        return {
            group_name for ad in self._assets_defs for group_name in ad.group_names_by_key.values()
        }

    def get_partitions_def(self, asset_key: AssetKey) -> Optional[PartitionsDefinition]:
        # Performing an existence check temporarily until we change callsites
        return self.get_assets_def(asset_key).partitions_def if self.has_asset(asset_key) else None

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
