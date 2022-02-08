from dagster import AssetKey, in_process_executor, multiprocess_executor, repository, resource
from dagster.core.asset_defs import AssetCollection, AssetIn, asset


def test_asset_repository():
    @asset(required_resource_keys={"the_resource"})
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

    @resource
    def the_resource():
        pass

    collection = AssetCollection.from_list(
        assets=[asset_foo, asset_bar, last_asset],
        resource_defs={"the_resource": the_resource},
        executor_def=in_process_executor,
    )

    @repository
    def the_repo():
        return [
            collection,
            collection.build_job("test", "asset_bar", executor_def=multiprocess_executor),
        ]

    mega_job = the_repo.get_all_jobs()[0]
    assert mega_job.name == "__REPOSITORY_MEGA_JOB"

    subset_job = the_repo.get_all_jobs()[1]
    assert subset_job.name == "test"
    assert len(subset_job.graph.solids) == 1
    assert subset_job.graph.solids[0].name == "asset_bar"

    result = collection.execute_in_process()
    assert result.success
