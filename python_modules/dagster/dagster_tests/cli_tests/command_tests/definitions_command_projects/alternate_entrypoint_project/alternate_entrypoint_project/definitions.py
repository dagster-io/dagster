import dagster as dg


@dg.asset
def my_asset() -> None: ...


my_job = dg.define_asset_job(name="my_job", selection="my_asset")

defs = dg.Definitions(assets=[my_asset], jobs=[my_job])
