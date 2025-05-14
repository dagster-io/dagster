from dagster import asset, define_asset_job
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.tags import EXTERNALLY_MANAGED_ASSETS_TAG


def create_job():
    @asset
    def my_asset():
        pass

    @asset
    def my_asset_2():
        pass

    my_job = define_asset_job(name="my_job", selection="*")

    return my_job.resolve(asset_graph=AssetGraph.from_assets([my_asset, my_asset_2]))


def test_externally_managed_assets() -> None:
    with instance_for_test() as instance:
        result = create_job().execute_in_process(
            instance=instance, tags={EXTERNALLY_MANAGED_ASSETS_TAG: "true"}
        )
        assert result.success
        assert result.get_asset_materialization_events() == []
        assert result.get_asset_materialization_planned_events() == []
