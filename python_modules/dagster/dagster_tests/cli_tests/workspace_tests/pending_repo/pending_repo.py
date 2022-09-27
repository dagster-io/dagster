from dagster import AssetKey, AssetsDefinition, op, repository
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionMetadata,
    CacheableAssetsDefinition,
)


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def get_metadata(self):
        return [
            AssetsDefinitionMetadata(
                keys_by_input_name={}, keys_by_output_name={"result": AssetKey(self.unique_id)}
            )
        ]

    def get_definitions(self, metadata):
        @op
        def my_op():
            return 1

        return [
            AssetsDefinition.from_op(
                my_op,
                keys_by_input_name=md.keys_by_input_name,
                keys_by_output_name=md.keys_by_output_name,
            )
            for md in metadata
        ]


@repository
def pending_repo():
    return [MyCacheableAssetsDefinition("abc")]
