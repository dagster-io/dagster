from dagster import AssetKey, AssetsDefinition, op, repository
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return [
            AssetsDefinitionCacheableData(
                keys_by_input_name={}, keys_by_output_name={"result": AssetKey(self.unique_id)}
            )
        ]

    def build_definitions(self, data):
        @op
        def my_op():
            return 1

        return [
            AssetsDefinition.from_op(
                my_op,
                keys_by_input_name=cd.keys_by_input_name,
                keys_by_output_name=cd.keys_by_output_name,
            )
            for cd in data
        ]


@repository
def pending_repo():
    return [MyCacheableAssetsDefinition("abc")]
