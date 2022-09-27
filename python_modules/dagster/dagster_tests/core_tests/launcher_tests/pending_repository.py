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
    AssetsDefinitionMetadata,
    CacheableAssetsDefinition,
)


class MyAssets(CacheableAssetsDefinition):
    def get_definitions(self, metadata):
        @op(name=f"my_op_{self.unique_id}", ins={"inp": In(Nothing)})
        def my_op():
            return 1

        return [
            AssetsDefinition.from_op(
                my_op,
                keys_by_input_name=md.keys_by_input_name,
                keys_by_output_name=md.keys_by_output_name,
                key_prefix=md.key_prefix,
                group_name=md.group_name,
                metadata_by_output_name=md.metadata_by_output_name,
            )
            for md in (metadata or [])
        ]

    def get_metadata(self):
        # used for tracking how many times we've executed this function
        instance = DagsterInstance.get()
        kvs_key = f"num_called_{self.unique_id}"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})

        return [
            AssetsDefinitionMetadata(
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


@asset
def c(foo_a, foo_b):
    return foo_a + foo_b + 1


@repository
def pending():
    return [MyAssets("a"), MyAssets("b"), c, define_asset_job("my_cool_asset_job")]
