# start_warehouse_instance
import dagster as dg
import dagster_airlift.core as dg_airlift_core

warehouse_airflow_instance = dg_airlift_core.AirflowInstance(
    auth_backend=dg_airlift_core.AirflowBasicAuthBackend(
        webserver_url="http://localhost:8081",
        username="admin",
        password="admin",
    ),
    name="warehouse",
)
# end_warehouse_instance

# start_load_all
assets = dg_airlift_core.load_airflow_dag_asset_specs(
    airflow_instance=warehouse_airflow_instance,
)
# end_load_all

# start_defs
defs = dg.Definitions(assets=assets)
# end_defs

# start_filter
load_customers = next(
    iter(
        dg_airlift_core.load_airflow_dag_asset_specs(
            airflow_instance=warehouse_airflow_instance,
            dag_selector_fn=lambda dag: dag.dag_id == "load_customers",
        )
    )
)
# end_filter

# start_customers_defs
defs = dg.Definitions(assets=[load_customers])
# end_customers_defs

# start_sensor
warehouse_sensor = dg_airlift_core.build_airflow_polling_sensor(
    mapped_assets=[load_customers],
    airflow_instance=warehouse_airflow_instance,
)
# end_sensor

# start_sensor_defs
defs = dg.Definitions(assets=[load_customers], sensors=[warehouse_sensor])
# end_sensor_defs

metrics_airflow_instance = dg_airlift_core.AirflowInstance(
    auth_backend=dg_airlift_core.AirflowBasicAuthBackend(
        webserver_url="http://localhost:8082",
        username="admin",
        password="admin",
    ),
    name="metrics",
)

customer_metrics_dag_asset = next(
    iter(
        dg_airlift_core.load_airflow_dag_asset_specs(
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

defs = dg.Definitions(assets=[load_customers, customer_metrics_dag_asset])
