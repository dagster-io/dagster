from dagster import resource, op, graph, ResourceDefinition


@op(required_resource_keys={"date", "s3_client", "snowflake_client"})
def upload_data():
    pass


@graph
def many_resources():
    upload_data()


many_resources_job = many_resources.to_job(
    partial=True, resource_defs={"date": ResourceDefinition.hardcoded_resource("2022-2-22")}
)

many_resources_default_set = {
    "s3_client": ResourceDefinition.hardcoded_resource("blah"),
    "snowflake_client": ResourceDefinition.hardcoded_resource("blah"),
}
