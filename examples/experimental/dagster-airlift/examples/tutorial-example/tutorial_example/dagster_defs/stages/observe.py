from dagster import AssetSpec, Definitions
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)

from .jaffle_shop import jaffle_shop_assets, jaffle_shop_resource


def rebuild_customer_list_defs() -> Definitions:
    return Definitions(
        assets=assets_with_task_mappings(
            dag_id="rebuild_customers_list",
            task_mappings={
                "load_raw_customers": [AssetSpec(key=["raw_data", "raw_customers"])],
                "build_dbt_models": [jaffle_shop_assets],
                "export_customers": [AssetSpec(key="customers_csv", deps=["customers"])],
            },
        ),
        resources={"dbt": jaffle_shop_resource()},
    )


defs = build_defs_from_airflow_instance(
    airflow_instance=AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    ),
    defs=rebuild_customer_list_defs(),
)
