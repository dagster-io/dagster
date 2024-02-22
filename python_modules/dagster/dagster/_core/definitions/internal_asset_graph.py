from typing import AbstractSet, Mapping, Optional, Sequence

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
from dagster._core.selector.subset_selector import DependencyGraph


class InternalAssetGraph(AssetGraph):
    def __init__(
        self,
        asset_dep_graph: DependencyGraph[AssetKey],
        source_asset_keys: AbstractSet[AssetKey],
        partitions_defs_by_key: Mapping[AssetKey, Optional[PartitionsDefinition]],
        partition_mappings_by_key: Mapping[AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]],
        group_names_by_key: Mapping[AssetKey, Optional[str]],
        freshness_policies_by_key: Mapping[AssetKey, Optional[FreshnessPolicy]],
        auto_materialize_policies_by_key: Mapping[AssetKey, Optional[AutoMaterializePolicy]],
        backfill_policies_by_key: Mapping[AssetKey, Optional[BackfillPolicy]],
        assets: Sequence[AssetsDefinition],
        source_assets: Sequence[SourceAsset],
        asset_checks: Sequence[AssetChecksDefinition],
        code_versions_by_key: Mapping[AssetKey, Optional[str]],
        is_observable_by_key: Mapping[AssetKey, bool],
        auto_observe_interval_minutes_by_key: Mapping[AssetKey, Optional[float]],
        required_assets_and_checks_by_key: Mapping[
            AssetKeyOrCheckKey, AbstractSet[AssetKeyOrCheckKey]
        ],
    ):
        super().__init__(
            asset_dep_graph=asset_dep_graph,
            source_asset_keys=source_asset_keys,
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            auto_materialize_policies_by_key=auto_materialize_policies_by_key,
            backfill_policies_by_key=backfill_policies_by_key,
            code_versions_by_key=code_versions_by_key,
            is_observable_by_key=is_observable_by_key,
            auto_observe_interval_minutes_by_key=auto_observe_interval_minutes_by_key,
            required_assets_and_checks_by_key=required_assets_and_checks_by_key,
        )
        self._assets = assets
        self._source_assets = source_assets
        self._asset_checks = asset_checks

        asset_check_keys = set()
        for asset_check in asset_checks:
            asset_check_keys.update([spec.key for spec in asset_check.specs])
        for asset in assets:
            asset_check_keys.update([spec.key for spec in asset.check_specs])
        self._asset_check_keys = asset_check_keys

    @property
    def asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self._asset_check_keys

    @property
    def assets(self) -> Sequence[AssetsDefinition]:
        return self._assets

    @property
    def source_assets(self) -> Sequence[SourceAsset]:
        return self._source_assets

    @property
    def asset_checks(self) -> Sequence[AssetChecksDefinition]:
        return self._asset_checks

    def includes_materializable_and_source_assets(self, asset_keys: AbstractSet[AssetKey]) -> bool:
        """Returns true if the given asset keys contains at least one materializable asset and
        at least one source asset.
        """
        selected_source_assets = self.source_asset_keys & asset_keys
        selected_regular_assets = asset_keys - self.source_asset_keys
        return len(selected_source_assets) > 0 and len(selected_regular_assets) > 0
