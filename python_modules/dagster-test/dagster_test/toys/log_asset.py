from dagster import In, Out, op, Array, Output
from dagster._legacy import pipeline, solid


@op(config_schema={"asset_key": Array(str), "pipeline": str})
def read_materialization(context):
    asset_key = context.op_config["asset_key"]
    from_pipeline = context.op_config["pipeline"]
    context.log.info(
        f"Found materialization for asset key {asset_key} in {from_pipeline}"
    )
    yield Output(asset_key)


@pipeline(
    description="Demo pipeline that logs asset materializations from other pipelines"
)
def log_asset_pipeline():
    read_materialization()
