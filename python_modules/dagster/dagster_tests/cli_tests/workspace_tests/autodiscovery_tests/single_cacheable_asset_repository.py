from dagster import repository
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition


class FooCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return []

    def build_definitions(self, *_args, **_kwargs):
        return []


@repository
def single_cacheable_asset_repository():
    return [FooCacheableAssetsDefinition("abc")]
