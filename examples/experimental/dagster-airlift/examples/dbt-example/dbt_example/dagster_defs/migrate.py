from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)

from dbt_example.dagster_defs.lakehouse import lakehouse_assets_def, lakehouse_existence_check
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME
from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions(
        assets=[
            *assets_with_task_mappings(
                dag_id="rebuild_iris_models",
                task_mappings={
                    "load_iris": [
                        lakehouse_assets_def(
                            csv_path=CSV_PATH,
                            duckdb_path=DB_PATH,
                            columns=IRIS_COLUMNS,
                        )
                    ],
                    "build_dbt_models": [jaffle_shop_assets],
                },
            )
        ],
        asset_checks=[lakehouse_existence_check(csv_path=CSV_PATH, duckdb_path=DB_PATH)],
        resources={"dbt": jaffle_shop_resource()},
    ),
)
