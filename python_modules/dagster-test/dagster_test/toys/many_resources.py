from dagster import ResourceDefinition, graph, op, resource


@op(required_resource_keys={"date", "s3_client", "snowflake_client"})
def upload_data():
    pass


@graph
def many_resources():
    upload_data()


many_resources_job = many_resources.to_job(
    partial=True, resource_defs={"date": ResourceDefinition.hardcoded_resource("2022-2-22")}
)


@resource(description="Lorem ipsum dolor sit amet")
def s3_client():
    pass


@resource(
    description="consectetur adipiscing elit", config_schema={"username": str, "password": str}
)
def snowflake_client():
    pass


many_resources_default_set = {
    "s3_client": s3_client,
    "snowflake_client": snowflake_client,
}
