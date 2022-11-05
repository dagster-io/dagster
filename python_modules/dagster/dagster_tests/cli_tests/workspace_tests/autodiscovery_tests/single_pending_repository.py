from dagster import repository
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition


@repository
def single_pending_repository():
    return [CacheableAssetsDefinition("abc")]
