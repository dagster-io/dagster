import os

from dagster import Definitions, asset, define_asset_job

if os.getenv("DAGSTER_IS_DEFS_VALIDATION_CLI"):

    @asset
    def my_gated_asset() -> None: ...

    my_gated_job = define_asset_job(name="my_gated_job", selection="my_gated_asset")

    defs = Definitions(assets=[my_gated_asset], jobs=[my_gated_job])
