from datetime import timedelta

from dagster import build_last_update_freshness_checks, build_sensor_for_freshness_checks
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    combine_defs,
    sync_build_defs_from_airflow_instance,
)
from dagster_airlift.dbt import specs_from_airflow_dbt

from dbt_example.dagster_defs.lakehouse import lakehouse_existence_check, specs_from_lakehouse
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH

from .constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    DBT_DAG_ASSET_KEY,
    PASSWORD,
    USERNAME,
    dbt_manifest_path,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)

# We expect the dbt dag to have completed within an hour of 9:00 AM every day
dbt_freshness_checks = build_last_update_freshness_checks(
    assets=[DBT_DAG_ASSET_KEY],
    lower_bound_delta=timedelta(hours=1),
    deadline_cron="0 9 * * *",
)
freshness_sensor = build_sensor_for_freshness_checks(
    freshness_checks=dbt_freshness_checks,
)
defs = sync_build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=combine_defs(
        *specs_from_lakehouse(
            dag_id="load_lakehouse",
            task_id="load_iris",
            csv_path=CSV_PATH,
        ),
        *specs_from_airflow_dbt(
            dag_id="dbt_dag",
            task_id="build_dbt_models",
            manifest=dbt_manifest_path(),
        ),
        lakehouse_existence_check(
            csv_path=CSV_PATH,
            duckdb_path=DB_PATH,
        ),
        *dbt_freshness_checks,
        freshness_sensor,
    ),
)
