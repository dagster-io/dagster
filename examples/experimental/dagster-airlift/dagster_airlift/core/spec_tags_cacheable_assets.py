import hashlib
import json
from typing import Any, Mapping

from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    CacheableAssetsDefinition,
    WrappedCacheableAssetsDefinition,
)


def spec_with_tags(spec: AssetSpec, tags: Mapping[str, str]) -> "AssetSpec":
    return spec._replace(tags={**spec.tags, **tags})


# Below is cargoculted from cacheable_assets.py
# Consider moving this there.
def _map_to_hashable(mapping: Mapping[Any, Any]) -> bytes:
    return json.dumps(
        {json.dumps(k, sort_keys=True): v for k, v in mapping.items()},
        sort_keys=True,
    ).encode("utf-8")


class SpecWithTagsCacheableAssetsDefinition(WrappedCacheableAssetsDefinition):
    def __init__(self, wrapped_def: CacheableAssetsDefinition, tags: Mapping[str, str]) -> None:
        self.tags = tags
        unique_id = f"spec_tags_wrapped_{wrapped_def.unique_id}_spec_with_tags_{self._get_hash()}"
        super().__init__(unique_id=unique_id, wrapped=wrapped_def)

    def transformed_assets_def(self, assets_def: AssetsDefinition) -> AssetsDefinition:
        return assets_def.map_asset_specs(lambda spec: spec_with_tags(spec, self.tags))

    def _get_hash(self) -> str:
        contents = hashlib.sha1()
        contents.update(_map_to_hashable(self.tags))
        return contents.hexdigest()
