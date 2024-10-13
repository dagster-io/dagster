from dagster import Definitions, MaterializeResult, asset, define_asset_job


@asset
def number_asset():
    yield MaterializeResult(
        metadata={
            "number": 1,
        }
    )


number_asset_job = define_asset_job(name="number_asset_job", selection="number_asset")

defs = Definitions(
    assets=[number_asset],
    jobs=[number_asset_job],
)
