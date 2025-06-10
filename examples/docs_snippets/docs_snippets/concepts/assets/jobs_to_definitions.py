import dagster as dg


@dg.asset
def number_asset():
    yield dg.MaterializeResult(
        metadata={
            "number": 1,
        }
    )


number_asset_job = dg.define_asset_job(
    name="number_asset_job", selection="number_asset"
)
