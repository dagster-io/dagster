from dagster import asset, execute_job, define_asset_job
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.instance_for_test import instance_for_test

def create_job():
    @asset
    def my_asset():
        pass

    @asset
    def my_asset_2():
        pass

    my_job = define_asset_job(name="my_job", selection="*")

    return my_job.resolve(asset_graph=AssetGraph.from_assets([my_asset, my_asset_2]))


def test_asset_events_as_engine_events() -> None:
    with instance_for_test() as instance:
        result = execute_job(reconstructable(create_job), instance=instance, asset_events_as_engine_events=True)
        assert result.success
        result
