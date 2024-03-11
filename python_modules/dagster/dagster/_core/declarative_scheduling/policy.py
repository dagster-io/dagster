from typing import TYPE_CHECKING, Optional

from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition


class SchedulingPolicy:
    METADATA_KEY = "dagster/scheduling_policy"
    ...

    @staticmethod
    def of_assets_def(
        assets_def: "AssetsDefinition", asset_key: Optional[CoercibleToAssetKey] = None
    ) -> Optional["SchedulingPolicy"]:
        asset_key = AssetKey.from_coercible(asset_key) if asset_key else assets_def.key
        value = assets_def.metadata_by_key[asset_key].get(SchedulingPolicy.METADATA_KEY)
        return value if isinstance(value, SchedulingPolicy) else None
