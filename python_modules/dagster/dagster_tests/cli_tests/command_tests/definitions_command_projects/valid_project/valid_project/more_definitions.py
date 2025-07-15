import dagster as dg


@dg.asset
def my_other_asset() -> None: ...


my_other_job = dg.define_asset_job(name="my_other_job", selection="my_other_asset")

defs = dg.Definitions(assets=[my_other_asset], jobs=[my_other_job])
