from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import AirflowInstance, BasicAuthBackend
from dagster_airlift.core.load_defs import build_defs_from_airflow_instance
from dagster_airlift.core.top_level_dag_def_api import proxying_dag_assets, proxying_task_assets

from dbt_example.dagster_defs.lakehouse import lakehouse_existence_check, specs_from_lakehouse
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME
from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions(
        assets=proxying_dag_assets(
            "rebuild_iris_models",
            proxying_task_assets(
                task_id="load_iris", assets=specs_from_lakehouse(csv_path=CSV_PATH)
            ),
            proxying_task_assets(task_id="build_dbt_models", assets=[jaffle_shop_assets]),
        ),
        asset_checks=[
            lakehouse_existence_check(
                csv_path=CSV_PATH,
                duckdb_path=DB_PATH,
            )
        ],
        resources={"dbt": jaffle_shop_resource()},
    ),
)
