from dagster import Array, MetadataValue, Output, graph, op


@op(config_schema={"asset_key": Array(str), "ops": str})
def read_materialization(context):
    asset_key = context.op_config["asset_key"]
    from_graph = context.op_config["graph"]
    context.log.info(f"Found materialization for asset key {asset_key} in {from_graph}")
    yield Output(asset_key)


@graph
def log_asset():
    read_materialization()


log_asset_job = log_asset.to_job(
    description="Demo job that logs asset materializations from graphs",
    job_tags={"owner": "person_2", "team": "cloud", "other": "goodbye"},
    metadata={
        "hello": "world",
        "baz": MetadataValue.text("aaaa"),
        "a_link": MetadataValue.url(url="https://google.com"),
    },
)
