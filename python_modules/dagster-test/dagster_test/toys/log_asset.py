from dagster import Array, Output
from dagster.legacy import pipeline, solid


@solid(config_schema={"asset_key": Array(str), "pipeline": str})
def read_materialization(context):
    asset_key = context.solid_config["asset_key"]
    from_pipeline = context.solid_config["pipeline"]
    context.log.info(f"Found materialization for asset key {asset_key} in {from_pipeline}")
    yield Output(asset_key)


@pipeline(description="Demo pipeline that logs asset materializations from other pipelines")
def log_asset_pipeline():
    read_materialization()
