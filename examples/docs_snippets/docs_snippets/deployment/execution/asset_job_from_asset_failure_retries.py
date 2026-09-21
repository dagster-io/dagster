import dagster as dg


@dg.asset
def asset_one(): ...


@dg.asset(deps=[asset_one])
def asset_two(): ...


@dg.asset(deps=[asset_two])
def asset_three(): ...


# start_from_asset_failure_job
asset_job = dg.define_asset_job(
    name="asset_job",
    selection=dg.AssetSelection.assets(asset_one, asset_two, asset_three),
    tags={
        "dagster/max_retries": "3",
        "dagster/retry_strategy": "FROM_ASSET_FAILURE",
        "dagster/retry_on_asset_or_op_failure": "false",
    },
)
# end_from_asset_failure_job
