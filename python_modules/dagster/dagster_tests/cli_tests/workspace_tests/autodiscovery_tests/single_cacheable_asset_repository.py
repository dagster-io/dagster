import dagster as dg
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    CacheableAssetsDefinition,
)


class FooCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return []

    def build_definitions(self, *_args, **_kwargs):
        return []


@dg.repository
def single_cacheable_asset_repository():
    return [FooCacheableAssetsDefinition("abc")]
