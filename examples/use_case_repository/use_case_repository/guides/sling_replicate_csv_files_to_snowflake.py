from dagster import Definitions, EnvVar
from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

S3_SOURCE_BUCKET = "elementl-data"


s3_connection = SlingConnectionResource(
    name="SLING_S3_SOURCE",
    type="s3",
    bucket=S3_SOURCE_BUCKET,
    access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
)

snowflake_connection = SlingConnectionResource(
    name="SLING_SNOWFLAKE_DESTINATION",
    type="snowflake",
    host=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
    database=EnvVar("SNOWFLAKE_DATABASE"),
    schema=EnvVar("SNOWFLAKE_SCHEMA"),
    role=EnvVar("SNOWFLAKE_ROLE"),
)


sling_resource = SlingResource(connections=[s3_connection, snowflake_connection])

replication_config = {
    "source": "SLING_S3_SOURCE",
    "target": "SLING_SNOWFLAKE_DESTINATION",
    "defaults": {"mode": "full-refresh", "object": "{stream_schema}_{stream_table}"},
    "streams": {
        f"s3://{S3_SOURCE_BUCKET}/staging": {
            "object": "public.example_table",
            "primary_key": "id",
        },
    },
}


@sling_assets(replication_config=replication_config)
def replicate_csv_to_snowflake(context, sling: SlingResource):
    yield from sling.replicate(context=context)


defs = Definitions(assets=[replicate_csv_to_snowflake], resources={"sling": sling_resource})
