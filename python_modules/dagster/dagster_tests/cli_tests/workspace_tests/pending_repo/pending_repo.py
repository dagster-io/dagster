from dagster import AssetKey, AssetsDefinition, op, repository
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition, CachedAssetsData


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def get_cached_data(self):
        return [
            CachedAssetsData(
                keys_by_input_name={}, keys_by_output_name={"result": AssetKey(self.unique_id)}
            )
        ]

    def get_definitions(self, cached_data):
        @op
        def my_op():
            return 1

        return [
            AssetsDefinition.from_op(
                my_op,
                keys_by_input_name=cd.keys_by_input_name,
                keys_by_output_name=cd.keys_by_output_name,
            )
            for cd in cached_data
        ]


@repository
def pending_repo():
    return [MyCacheableAssetsDefinition("abc")]
