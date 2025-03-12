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

metrics_airflow_instance = dg_airlift_core.AirflowInstance(
    auth_backend=dg_airlift_core.AirflowBasicAuthBackend(
        webserver_url="http://localhost:8082",
        username="admin",
        password="admin",
    ),
    name="metrics",
)

load_customers_dag_asset = next(
    iter(
        dg_airlift_core.load_airflow_dag_asset_specs(
            airflow_instance=warehouse_airflow_instance,
            dag_selector_fn=lambda dag: dag.dag_id == "load_customers",
        )
    )
)
customer_metrics_dag_asset = next(
    iter(
        dg_airlift_core.load_airflow_dag_asset_specs(
            airflow_instance=metrics_airflow_instance,
            dag_selector_fn=lambda dag: dag.dag_id == "customer_metrics",
        )
    )
).replace_attributes(
    deps=[load_customers_dag_asset],
    automation_condition=dg.AutomationCondition.eager(),
)

warehouse_sensor = dg_airlift_core.build_airflow_polling_sensor(
    mapped_assets=[load_customers_dag_asset],
    airflow_instance=warehouse_airflow_instance,
)
metrics_sensor = dg_airlift_core.build_airflow_polling_sensor(
    mapped_assets=[customer_metrics_dag_asset],
    airflow_instance=metrics_airflow_instance,
)


# start_multi_asset
@dg.multi_asset(specs=[customer_metrics_dag_asset])
def run_customer_metrics() -> dg.MaterializeResult:
    run_id = metrics_airflow_instance.trigger_dag("customer_metrics")
    metrics_airflow_instance.wait_for_run_completion("customer_metrics", run_id)
    if metrics_airflow_instance.get_run_state("customer_metrics", run_id) == "success":
        return dg.MaterializeResult(asset_key=customer_metrics_dag_asset.key)
    else:
        raise Exception("Dag run failed.")


# end_multi_asset

# start_multi_asset_defs
defs = dg.Definitions(
    assets=[load_customers_dag_asset, run_customer_metrics],
    sensors=[warehouse_sensor, metrics_sensor],
)
# end_multi_asset_defs

# start_eager
customer_metrics_dag_asset = customer_metrics_dag_asset.replace_attributes(
    automation_condition=dg.AutomationCondition.eager(),
)
# end_eager

# start_automation_sensor
automation_sensor = dg.AutomationConditionSensorDefinition(
    name="automation_sensor",
    target="*",
    default_status=dg.DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=1,
)
# end_automation_sensor

# start_complete_defs
defs = dg.Definitions(
    assets=[load_customers_dag_asset, run_customer_metrics],
    sensors=[warehouse_sensor, metrics_sensor, automation_sensor],
)
# end_complete_defs
