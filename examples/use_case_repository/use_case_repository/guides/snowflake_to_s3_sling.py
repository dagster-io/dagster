# pyright: reportCallIssue=none
# pyright: reportOptionalMemberAccess=none

from dagster import Definitions, EnvVar
from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

# Step 2: Define Sling Connections
s3_connection = SlingConnectionResource(
    name="MY_S3",
    type="s3",
    bucket="your-s3-bucket",
    access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
)

snowflake_connection = SlingConnectionResource(
    name="MY_SNOWFLAKE",
    type="snowflake",
    host="your-snowflake-host",
    user="your-snowflake-user",
    database="your-snowflake-database",
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    role="your-snowflake-role",
)

sling_resource = SlingResource(connections=[s3_connection, snowflake_connection])

# Step 3: Define the Data Ingestion Asset
replication_config = {
    "SOURCE": "MY_S3",
    "TARGET": "MY_SNOWFLAKE",
    "defaults": {"mode": "full-refresh", "object": "{stream_schema}_{stream_table}"},
    "streams": {
        "s3://your-s3-bucket/your-file.csv": {
            "object": "your_snowflake_schema.your_table",
            "primary_key": "id",
        },
    },
}


@sling_assets(replication_config=replication_config)
def ingest_s3_to_snowflake(context, sling: SlingResource):
    yield from sling.replicate(context=context)


defs = Definitions(assets=[ingest_s3_to_snowflake], resources={"sling": sling_resource})
