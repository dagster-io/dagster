# start_warehouse_instance
from dagster_airlift.core import AirflowBasicAuthBackend, AirflowInstance

warehouse_airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8081",
        username="admin",
        password="admin",
    ),
    name="warehouse",
)
# end_warehouse_instance

# start_load_all
from dagster_airlift.core import load_airflow_dag_asset_specs

assets = load_airflow_dag_asset_specs(
    airflow_instance=warehouse_airflow_instance,
)
# end_load_all

# start_defs
from dagster import Definitions

defs = Definitions(assets=assets)
# end_defs

# start_filter
load_customers = next(
    iter(
        load_airflow_dag_asset_specs(
            airflow_instance=warehouse_airflow_instance,
            dag_selector_fn=lambda dag: dag.dag_id == "load_customers",
        )
    )
)
# end_filter

# start_customers_defs
defs = Definitions(assets=[load_customers])
# end_customers_defs

# start_sensor
from dagster_airlift.core import build_airflow_polling_sensor

warehouse_sensor = build_airflow_polling_sensor(
    mapped_assets=[load_customers],
    airflow_instance=warehouse_airflow_instance,
)
# end_sensor

# start_sensor_defs
defs = Definitions(assets=[load_customers], sensors=[warehouse_sensor])
# end_sensor_defs

metrics_airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8082",
        username="admin",
        password="admin",
    ),
    name="metrics",
)

customer_metrics_dag_asset = next(
    iter(
        load_airflow_dag_asset_specs(
            airflow_instance=metrics_airflow_instance,
            dag_selector_fn=lambda dag: dag.dag_id == "customer_metrics",
        )
    )
)

# start_lineage
customer_metrics_dag_asset = customer_metrics_dag_asset.replace_attributes(
    deps=[load_customers],
)
# end_lineage

defs = Definitions(assets=[load_customers, customer_metrics_dag_asset])
