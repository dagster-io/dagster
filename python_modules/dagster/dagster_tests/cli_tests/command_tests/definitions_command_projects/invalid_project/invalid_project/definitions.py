from dagster import Definitions, asset, define_asset_job


@asset(name="my_asset")
def my_first_asset() -> None: ...


@asset(name="my_asset")
def my_second_asset() -> None: ...


my_job = define_asset_job(name="my_job", selection="my_asset")

defs = Definitions(assets=[my_first_asset, my_second_asset], jobs=[my_job])
