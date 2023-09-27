from dagster import Definitions, asset, define_asset_job


@asset
def number_asset():
    return [1, 2, 3]


number_asset_job = define_asset_job(name="number_asset_job", selection="number_asset")

defs = Definitions(
    assets=[number_asset],
    jobs=[number_asset_job],
)
