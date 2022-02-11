import pytest
from dagster import (
    AssetKey,
    DagsterInvalidDefinitionError,
    IOManager,
    in_process_executor,
    io_manager,
    repository,
    resource,
)
from dagster.core.asset_defs import AssetCollection, AssetIn, ForeignAsset, asset


def test_asset_collection_from_list():
    @asset
    def asset_foo():
        return "foo"

    @asset
    def asset_bar():
        return "bar"

    @asset(ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))})
    def last_asset(asset_bar):
        return asset_bar

    collection = AssetCollection.from_list(assets=[asset_foo, asset_bar, last_asset])

    @repository
    def the_repo():
        return [collection]

    assert len(the_repo.get_all_jobs()) == 1
    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_collection_underlying_job.name == "__ASSET_COLLECTION"

    result = asset_collection_underlying_job.execute_in_process()
    assert result.success


def test_asset_collection_foreign_asset():
    foo_fa = ForeignAsset(key=AssetKey("foo"), io_manager_key="the_manager")

    @asset
    def asset_depends_on_source(foo):
        return foo

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    @repository
    def the_repo():
        return [
            AssetCollection.from_list(
                assets=[asset_depends_on_source],
                source_assets=[foo_fa],
                resource_defs={"the_manager": the_manager},
            )
        ]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_collection_underlying_job.name == "__ASSET_COLLECTION"

    result = asset_collection_underlying_job.execute_in_process()
    assert result.success


def test_asset_collection_with_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    @resource
    def the_resource():
        return "foo"

    @repository
    def the_repo():
        return [AssetCollection.from_list([asset_foo], resource_defs={"foo": the_resource})]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_collection_underlying_job.name == "__ASSET_COLLECTION"

    result = asset_collection_underlying_job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_foo") == "foo"


def test_asset_collection_missing_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"AssetCollection is missing required resource keys for asset 'asset_foo'. Missing resource keys: \['foo'\]",
    ):
        AssetCollection.from_list([asset_foo])


def test_asset_collection_with_executor():
    @asset
    def the_asset():
        pass

    @repository
    def the_repo():
        return [AssetCollection.from_list([the_asset], executor_def=in_process_executor)]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert (
        asset_collection_underlying_job.executor_def  # pylint: disable=comparison-with-callable
        == in_process_executor
    )
