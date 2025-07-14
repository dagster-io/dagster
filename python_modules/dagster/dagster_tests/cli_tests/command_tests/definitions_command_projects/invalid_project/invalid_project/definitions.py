import dagster as dg


@dg.asset(name="my_asset")
def my_first_asset() -> None: ...


@dg.asset(name="my_asset")
def my_second_asset() -> None: ...


my_job = dg.define_asset_job(name="my_job", selection="my_asset")

defs = dg.Definitions(assets=[my_first_asset, my_second_asset], jobs=[my_job])
