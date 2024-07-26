import os

from dagster import Definitions
from dagster_airlift import (
    airflow_task_mappings_from_dbt_project,
    assets_defs_from_airflow_instance,
    build_airflow_polling_sensor,
)

# Airflow instance running at localhost:8080
AIRFLOW_BASE_URL = "http://localhost:8080"
AIRFLOW_INSTANCE_NAME = "my_airflow_instance"

# Authentication credentials (lol)
USERNAME = "admin"
PASSWORD = "admin"

manifest_path = os.path.join(os.environ["DBT_PROJECT_DIR"], "target", "manifest.json")


airflow_assets = assets_defs_from_airflow_instance(
    airflow_webserver_url=AIRFLOW_BASE_URL,
    auth=(USERNAME, PASSWORD),
    instance_name=AIRFLOW_INSTANCE_NAME,
    task_maps=[
        *airflow_task_mappings_from_dbt_project(
            dbt_manifest_path=manifest_path,
            airflow_instance_name=AIRFLOW_INSTANCE_NAME,
            dag_id="dbt_dag",
            task_id="build_dbt_models",
        ),
    ],
)
airflow_sensor = build_airflow_polling_sensor(
    airflow_webserver_url=AIRFLOW_BASE_URL,
    auth=(USERNAME, PASSWORD),
    airflow_asset_specs=[spec for asset in airflow_assets for spec in asset.specs],
)

defs = Definitions(
    assets=airflow_assets,
    sensors=[airflow_sensor],
)
