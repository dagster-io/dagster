import os

from dagster_dbt import dbt_cloud_resource, load_assets_from_dbt_cloud_job

import dagster as dg

# set the auth token as an env var for demo purposes
os.environ["DBT_CLOUD_AUTH_TOKEN"] = "abc"

# configure a resource to connect to your dbt Cloud instance
dbt_cloud = dbt_cloud_resource.configured(
    {"auth_token": {"env": "DBT_CLOUD_AUTH_TOKEN"}, "account_id": 11111}
)

# import assets from dbt
dbt_cloud_assets = load_assets_from_dbt_cloud_job(
    dbt_cloud=dbt_cloud,
    job_id=33333,
)

defs = dg.Definitions(assets=[dbt_cloud_assets])
