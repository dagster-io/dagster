# pyright: reportCallIssue=none
# pyright: reportOptionalMemberAccess=none

# start_storage_config
from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

from dagster import EnvVar

target = SlingConnectionResource(
    name="MY_SF",
    type="snowflake",
    host="hostname.snowflake",
    user="username",
    database="database",
    password=EnvVar("SF_PASSWORD"),
    role="role",
)

source = SlingConnectionResource(
    name="MY_S3",
    type="s3",
    bucket="sling-bucket",
    access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
)

sling = SlingResource(connections=[source, target])

replication_config = {
    "SOURCE": "MY_S3",
    "TARGET": "MY_SF",
    "defaults": {"mode": "full-refresh", "object": "{stream_schema}_{stream_table}"},
    "streams": {
        "s3://my-bucket/my_file.parquet": {
            "object": "marts.my_table",
            "primary_key": "id",
        },
    },
}


@sling_assets(replication_config=replication_config)
def my_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)


# end_storage_config
