from dagster import Definitions, asset, define_asset_job


@asset
def my_asset() -> None: ...


my_job = define_asset_job(name="my_job", selection="my_asset")

defs = Definitions(assets=[my_asset], jobs=[my_job])
