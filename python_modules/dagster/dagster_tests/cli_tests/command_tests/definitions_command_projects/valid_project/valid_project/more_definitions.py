from dagster import Definitions, asset, define_asset_job


@asset
def my_other_asset() -> None: ...


my_other_job = define_asset_job(name="my_other_job", selection="my_other_asset")

defs = Definitions(assets=[my_other_asset], jobs=[my_other_job])
