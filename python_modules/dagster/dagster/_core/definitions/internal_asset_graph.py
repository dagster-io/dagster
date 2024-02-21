from typing import AbstractSet, Dict, Iterable, List, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_graph import AssetGraph, AssetKeyOrCheckKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.selector.subset_selector import DependencyGraph, generate_asset_dep_graph


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

    @staticmethod
    def from_assets(
        all_assets: Iterable[Union[AssetsDefinition, SourceAsset]],
        asset_checks: Optional[Sequence[AssetChecksDefinition]] = None,
    ) -> "InternalAssetGraph":
        from dagster._core.definitions.internal_asset_graph import InternalAssetGraph

        assets_defs: List[AssetsDefinition] = []
        source_assets: List[SourceAsset] = []
        partitions_defs_by_key: Dict[AssetKey, Optional[PartitionsDefinition]] = {}
        partition_mappings_by_key: Dict[
            AssetKey, Optional[Mapping[AssetKey, PartitionMapping]]
        ] = {}
        group_names_by_key: Dict[AssetKey, Optional[str]] = {}
        freshness_policies_by_key: Dict[AssetKey, Optional[FreshnessPolicy]] = {}
        auto_materialize_policies_by_key: Dict[AssetKey, Optional[AutoMaterializePolicy]] = {}
        backfill_policies_by_key: Dict[AssetKey, Optional[BackfillPolicy]] = {}
        code_versions_by_key: Dict[AssetKey, Optional[str]] = {}
        is_observable_by_key: Dict[AssetKey, bool] = {}
        auto_observe_interval_minutes_by_key: Dict[AssetKey, Optional[float]] = {}
        required_assets_and_checks_by_key: Dict[
            AssetKeyOrCheckKey, AbstractSet[AssetKeyOrCheckKey]
        ] = {}

        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
                partitions_defs_by_key[asset.key] = asset.partitions_def
                group_names_by_key[asset.key] = asset.group_name
                is_observable_by_key[asset.key] = asset.is_observable
                auto_observe_interval_minutes_by_key[
                    asset.key
                ] = asset.auto_observe_interval_minutes
            else:  # AssetsDefinition
                assets_defs.append(asset)
                partition_mappings_by_key.update(
                    {key: asset.partition_mappings for key in asset.keys}
                )
                partitions_defs_by_key.update({key: asset.partitions_def for key in asset.keys})
                group_names_by_key.update(asset.group_names_by_key)
                freshness_policies_by_key.update(asset.freshness_policies_by_key)
                auto_materialize_policies_by_key.update(asset.auto_materialize_policies_by_key)
                backfill_policies_by_key.update({key: asset.backfill_policy for key in asset.keys})
                code_versions_by_key.update(asset.code_versions_by_key)

                is_observable = asset.execution_type == AssetExecutionType.OBSERVATION
                is_observable_by_key.update({key: is_observable for key in asset.keys})

                # Set auto_observe_interval_minutes for external observable assets
                # This can be removed when/if we have a a solution for mapping
                # `auto_observe_interval_minutes` to an AutoMaterialzePolicy
                auto_observe_interval_minutes_by_key.update(
                    {key: asset.auto_observe_interval_minutes for key in asset.keys}
                )

                if not asset.can_subset:
                    all_required_keys = {*asset.check_keys, *asset.keys}
                    if len(all_required_keys) > 1:
                        for key in all_required_keys:
                            required_assets_and_checks_by_key[key] = all_required_keys

        return InternalAssetGraph(
            asset_dep_graph=generate_asset_dep_graph(assets_defs, source_assets),
            source_asset_keys={source_asset.key for source_asset in source_assets},
            partitions_defs_by_key=partitions_defs_by_key,
            partition_mappings_by_key=partition_mappings_by_key,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            auto_materialize_policies_by_key=auto_materialize_policies_by_key,
            backfill_policies_by_key=backfill_policies_by_key,
            assets=assets_defs,
            asset_checks=asset_checks or [],
            source_assets=source_assets,
            code_versions_by_key=code_versions_by_key,
            is_observable_by_key=is_observable_by_key,
            auto_observe_interval_minutes_by_key=auto_observe_interval_minutes_by_key,
            required_assets_and_checks_by_key=required_assets_and_checks_by_key,
        )

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
