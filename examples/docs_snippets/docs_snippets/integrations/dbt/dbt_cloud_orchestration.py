# ruff: isort: skip_file
import os

import dagster as dg
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace
from dagster_dbt.cloud_v2.sensor_builder import build_dbt_cloud_polling_sensor

# Define credentials
creds = DbtCloudCredentials(
    account_id=os.getenv("DBT_CLOUD_ACCOUNT_ID"),
    access_url=os.getenv("DBT_CLOUD_ACCESS_URL"),
    token=os.getenv("DBT_CLOUD_TOKEN"),
)

# Define the worskpace
workspace = DbtCloudWorkspace(
    credentials=creds,
    project_id=os.getenv("DBT_CLOUD_PROJECT_ID"),
    environment_id=os.getenv("DBT_CLOUD_ENVIRONMENT_ID"),
)


# Builds your asset graph in a materializable way
@dbt_cloud_assets(workspace=workspace)
def my_dbt_cloud_assets(
    context: dg.AssetExecutionContext, dbt_cloud: DbtCloudWorkspace
):
    yield from dbt_cloud.cli(args=["build"], context=context).wait()


# Automates your assets using Declarative Automation
# https://docs.dagster.io/guides/automate/declarative-automation
my_dbt_cloud_assets = my_dbt_cloud_assets.map_asset_specs(
    lambda spec: spec.replace_attributes(
        automation_condition=dg.AutomationCondition.eager()
    )
)
# Adds these assets to the Declarative Automation Sensor
automation_sensor = dg.AutomationConditionSensorDefinition(
    name="automation_sensor",
    target="*",
    default_status=dg.DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=1,
)

# Build a sensor which will poll dbt Cloud for updates on runs/materialization history
# and dbt Cloud Assets
dbt_cloud_polling_sensor = build_dbt_cloud_polling_sensor(workspace=workspace)
