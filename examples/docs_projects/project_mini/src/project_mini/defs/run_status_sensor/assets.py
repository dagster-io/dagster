import dagster as dg


@dg.asset
def first_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info("First asset")


@dg.asset
def second_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info("Second asset")


@dg.asset
def third_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info("Third asset")


# Define the upstream jobs
upstream_job_1 = dg.define_asset_job(name="upstream_job_1", selection="first_asset")

upstream_job_2 = dg.define_asset_job(name="upstream_job_2", selection="second_asset")

downstream_job = dg.define_asset_job(name="downstream_job", selection="third_asset")
