from dagster import AssetKey, DagsterInstance, asset, define_asset_job, repository
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionMetadata,
    CacheableAssetsDefinition,
)


class MyAssets(CacheableAssetsDefinition):
    def get_definitions(self, metadata):
        def _asset_from_metadata(md):
            @asset(name=list(md.output_keys)[0].path[-1], non_argument_deps=md.input_keys)
            def _asset():
                return 1

            return _asset

        return [_asset_from_metadata(md) for md in (metadata or [])]

    def get_metadata(self):
        # used for tracking how many times we've executed this function
        instance = DagsterInstance.get()
        kvs_key = f"num_called_{self.unique_id}"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})

        return [
            AssetsDefinitionMetadata(
                input_keys={AssetKey(f"upstream_{self.unique_id}")},
                output_keys={AssetKey(f"foo_{self.unique_id}")},
            )
        ]


@asset
def c(foo_a, foo_b):
    return foo_a + foo_b + 1


@repository
def pending():
    return [MyAssets("a"), MyAssets("b"), c, define_asset_job("my_cool_asset_job")]
