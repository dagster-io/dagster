from datetime import timedelta

from dagster import build_last_update_freshness_checks, build_sensor_for_freshness_checks
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)
from dagster_dbt.asset_specs import build_dbt_asset_specs

from dbt_example.dagster_defs.lakehouse import lakehouse_existence_check_defs, specs_from_lakehouse
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


def freshness_defs() -> Definitions:
    dbt_freshness_checks = build_last_update_freshness_checks(
        assets=[DBT_DAG_ASSET_KEY],
        lower_bound_delta=timedelta(hours=1),
        deadline_cron="0 9 * * *",
    )
    return Definitions(
        asset_checks=dbt_freshness_checks,
        sensors=[
            build_sensor_for_freshness_checks(
                freshness_checks=dbt_freshness_checks,
            )
        ],
    )


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions.merge(
        dag_defs(
            "rebuild_iris_models",
            task_defs("load_iris", Definitions(assets=specs_from_lakehouse(csv_path=CSV_PATH))),
            task_defs(
                "build_dbt_models",
                Definitions(assets=build_dbt_asset_specs(manifest=dbt_manifest_path())),
            ),
        ),
        lakehouse_existence_check_defs(
            csv_path=CSV_PATH,
            duckdb_path=DB_PATH,
        ),
        freshness_defs(),
    ),
)
