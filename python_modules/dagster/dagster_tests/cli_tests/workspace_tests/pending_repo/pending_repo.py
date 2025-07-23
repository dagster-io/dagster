import dagster as dg
from dagster import AssetsDefinition
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        return [
            AssetsDefinitionCacheableData(
                keys_by_input_name={}, keys_by_output_name={"result": dg.AssetKey(self.unique_id)}
            )
        ]

    def build_definitions(self, data):
        @dg.op
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


@dg.repository
def pending_repo():
    return [MyCacheableAssetsDefinition("abc")]
