from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)

from dbt_example.dagster_defs.lakehouse import specs_from_lakehouse
from dbt_example.shared.load_iris import CSV_PATH

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME
from .jaffle_shop import jaffle_shop_external_assets, jaffle_shop_resource

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions(
        assets=assets_with_task_mappings(
            dag_id="rebuild_iris_models",
            task_mappings={
                "load_iris": specs_from_lakehouse(csv_path=CSV_PATH),
                "build_dbt_models": jaffle_shop_external_assets,
            },
        ),
        resources={"dbt": jaffle_shop_resource()},
    ),
    sensor_minimum_interval_seconds=1,
)
