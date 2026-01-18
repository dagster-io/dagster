import dagster as dg
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.storage.tags import EXTERNALLY_MANAGED_ASSETS_TAG


def create_job():
    @dg.asset
    def my_asset():
        pass

    @dg.asset
    def my_asset_2():
        pass

    my_job = dg.define_asset_job(name="my_job", selection="*")

    return my_job.resolve(asset_graph=AssetGraph.from_assets([my_asset, my_asset_2]))


def test_externally_managed_assets() -> None:
    with dg.instance_for_test() as instance:
        result = create_job().execute_in_process(
            instance=instance, tags={EXTERNALLY_MANAGED_ASSETS_TAG: "true"}
        )
        assert result.success
        assert result.get_asset_materialization_events() == []
        assert result.get_asset_materialization_planned_events() == []
