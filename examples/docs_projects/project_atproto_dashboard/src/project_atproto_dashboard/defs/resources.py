import dagster as dg
from dagster_aws.s3 import S3Resource
from dagster_dbt import DbtCliResource

from project_atproto_dashboard.defs.atproto import ATProtoResource
from project_atproto_dashboard.defs.dashboard import power_bi_workspace
from project_atproto_dashboard.defs.modeling import dbt_project

dbt_resource = DbtCliResource(project_dir=dbt_project)


atproto_resource = ATProtoResource(
    login=dg.EnvVar("BSKY_LOGIN"), password=dg.EnvVar("BSKY_APP_PASSWORD")
)

s3_resource = S3Resource(
    endpoint_url=dg.EnvVar("AWS_ENDPOINT_URL"),
    aws_access_key_id=dg.EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=dg.EnvVar("AWS_SECRET_ACCESS_KEY"),
    region_name="auto",
)


# start_def
@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "dbt": dbt_resource,
            "power_bi": power_bi_workspace,
            "atproto_resource": atproto_resource,
            "s3_resource": s3_resource,
        }
    )


# end_def
