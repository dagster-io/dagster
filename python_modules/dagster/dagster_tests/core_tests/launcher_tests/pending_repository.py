from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
    In,
    MetadataValue,
    Nothing,
    asset,
    define_asset_job,
    op,
    repository,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)


class MyAssets(CacheableAssetsDefinition):
    def compute_cacheable_data(self):
        # used for tracking how many times we've executed this function
        instance = DagsterInstance.get()
        kvs_key = f"compute_cacheable_data_called_{self.unique_id}"
        compute_cacheable_data_called = int(
            instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0")
        )
        instance.run_storage.kvs_set({kvs_key: str(compute_cacheable_data_called + 1)})

        return [
            AssetsDefinitionCacheableData(
                keys_by_input_name={"inp": AssetKey(f"upstream_{self.unique_id}")},
                keys_by_output_name={"result": AssetKey(f"foo_{self.unique_id}")},
                internal_asset_deps={"result": {AssetKey(f"upstream_{self.unique_id}")}},
                group_name="some_group",
                metadata_by_output_name={
                    "result": {
                        "a": 1,
                        "b": "foo",
                        "c": 1.75,
                        "d": MetadataValue.md("### something \n```\na\n```"),
                        "e": {"foo": "bar", "baz": 1},
                    },
                },
                can_subset=False,
                extra_metadata={"foo": None, "bar": {"hi": 1.75, "x": ["y", {"z": "w"}, 2]}},
            )
        ]

    def build_definitions(self, data):
        # used for tracking how many times we've executed this function
        instance = DagsterInstance.get()
        kvs_key = f"get_definitions_called_{self.unique_id}"
        get_definitions_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(get_definitions_called + 1)})

        @op(name=f"my_op_{self.unique_id}", ins={"inp": In(Nothing)})
        def my_op():
            return 1

        return [
            AssetsDefinition.from_op(
                my_op,
                keys_by_input_name=cd.keys_by_input_name,
                keys_by_output_name=cd.keys_by_output_name,
                key_prefix=cd.key_prefix,
                group_name=cd.group_name,
                metadata_by_output_name=cd.metadata_by_output_name,
            )
            for cd in (data or [])
        ]


@asset
def c(foo_a, foo_b):
    return foo_a + foo_b + 1


@repository
def pending():
    return [MyAssets("a"), MyAssets("b"), c, define_asset_job("my_cool_asset_job")]
