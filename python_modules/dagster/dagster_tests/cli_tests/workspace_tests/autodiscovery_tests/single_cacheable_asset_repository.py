import dagster as dg
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition


class FooCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return []

    def build_definitions(self, *_args, **_kwargs):
        return []


@dg.repository
def single_cacheable_asset_repository():
    return [FooCacheableAssetsDefinition("abc")]
