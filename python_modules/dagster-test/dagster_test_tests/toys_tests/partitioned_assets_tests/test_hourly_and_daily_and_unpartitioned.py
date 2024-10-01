from dagster import Definitions, load_assets_from_modules
from dagster._core.definitions.asset_key import AssetKey
from dagster_test.toys.partitioned_assets import hourly_and_daily_and_unpartitioned


def test_assets():
    defs = Definitions(assets=load_assets_from_modules([hourly_and_daily_and_unpartitioned]))
    job_def = defs.get_implicit_global_asset_job_def()

    assert job_def.execute_in_process(
        asset_selection=[
            AssetKey(["upstream_daily_partitioned_asset"]),
            AssetKey(["downstream_daily_partitioned_asset"]),
        ],
        partition_key="2020-01-01",
    ).success
    assert job_def.execute_in_process(
        asset_selection=[AssetKey(["hourly_partitioned_asset"])], partition_key="2022-03-12-00:00"
    ).success
