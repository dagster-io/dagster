import os

import dagster as dg

if os.getenv("DAGSTER_IS_DEFS_VALIDATION_CLI"):

    @dg.asset
    def my_gated_asset() -> None: ...

    my_gated_job = dg.define_asset_job(name="my_gated_job", selection="my_gated_asset")

    defs = dg.Definitions(assets=[my_gated_asset], jobs=[my_gated_job])
