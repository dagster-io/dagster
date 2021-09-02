from dagster import Array, Output, graph, op


@op(config_schema={"asset_key": Array(str), "graph": str})
def read_materialization(context):
    asset_key = context.op_config["asset_key"]
    from_graph = context.op_config["graph"]
    context.log.info(f"Found materialization for asset key {asset_key} in {from_graph}")
    yield Output(asset_key)


@graph
def log_asset_graph():
    read_materialization()


log_asset_job = log_asset_graph.to_job(
    description="Demo job that logs asset materializations from graphs"
)
