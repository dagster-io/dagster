from datetime import timedelta

from dagster import (
    Definitions,
    build_last_update_freshness_checks,
    build_sensor_for_freshness_checks,
)
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, assets_with_task_mappings

from dbt_example.dagster_defs.lakehouse import lakehouse_existence_check, specs_from_lakehouse
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH

from .constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    DBT_DAG_ASSET_KEY,
    PASSWORD,
    USERNAME,
)
from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)

dbt_freshness_checks = build_last_update_freshness_checks(
    assets=[DBT_DAG_ASSET_KEY],
    lower_bound_delta=timedelta(hours=1),
    deadline_cron="0 9 * * *",
)

defs = Definitions(
    assets=assets_with_task_mappings(
        dag_id="rebuild_iris_models",
        task_mappings={
            "load_iris": specs_from_lakehouse(csv_path=CSV_PATH),
            "build_dbt_models": [jaffle_shop_assets],
        },
    ),
    asset_checks=[
        lakehouse_existence_check(
            csv_path=CSV_PATH,
            duckdb_path=DB_PATH,
        ),
        *dbt_freshness_checks,
    ],
    sensors=[
        build_sensor_for_freshness_checks(
            freshness_checks=dbt_freshness_checks,
        ),
    ],
    resources={"dbt": jaffle_shop_resource()},
)
