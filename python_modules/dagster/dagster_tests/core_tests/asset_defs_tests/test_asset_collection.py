from dagster import (
    AssetKey,
    IOManager,
    in_process_executor,
    io_manager,
    multiprocess_executor,
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

    @asset(
        ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))}
    )  # should still use output from asset_foo
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
    pass


def test_asset_collection_missing_resources():
    pass


def test_asset_collection_with_executor():
    pass


# def test_asset_repository():
#     @asset(required_resource_keys={"the_resource"})
#     def asset_foo():
#         return "foo"

#     @asset
#     def asset_bar():
#         return "bar"

#     @asset(
#         ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))}
#     )  # should still use output from asset_foo
#     def last_asset(asset_bar):
#         return asset_bar

#     @resource
#     def the_resource():
#         pass

#     collection = AssetCollection.from_list(
#         assets=[asset_foo, asset_bar, last_asset],
#         resource_defs={"the_resource": the_resource},
#         executor_def=in_process_executor,
#     )

#     @repository
#     def the_repo():
#         return [
#             collection,
#             collection.build_job("test", "asset_bar", executor_def=multiprocess_executor),
#         ]

#     mega_job = the_repo.get_all_jobs()[0]
#     assert mega_job.name == "__REPOSITORY_MEGA_JOB"

#     subset_job = the_repo.get_all_jobs()[1]
#     assert subset_job.name == "test"
#     assert len(subset_job.graph.solids) == 1
#     assert subset_job.graph.solids[0].name == "asset_bar"

#     result = collection.execute_in_process()
#     assert result.success
