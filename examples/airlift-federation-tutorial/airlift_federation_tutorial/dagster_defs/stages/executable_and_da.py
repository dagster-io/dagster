import dagster_airlift.core.predicates as predicates
from dagster import (
    AutomationConditionSensorDefinition,
    DefaultSensorStatus,
    Definitions,
    MaterializeResult,
    multi_asset,
)
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    build_airflow_polling_sensor,
    load_airflow_dag_asset_specs,
)

warehouse_airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8081",
        username="admin",
        password="admin",
    ),
    name="warehouse",
)

metrics_airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8082",
        username="admin",
        password="admin",
    ),
    name="metrics",
)

warehouse_specs = load_airflow_dag_asset_specs(
    airflow_instance=warehouse_airflow_instance,
)

is_customer_metrics = predicates.dag_name_in({"customer_metrics"})
is_load_customers = predicates.dag_name_in({"load_customers"})
metrics_specs = load_airflow_dag_asset_specs(
    airflow_instance=metrics_airflow_instance,
).merge_attributes({"deps": warehouse_specs.filter(is_load_customers)}, where=is_customer_metrics)

customer_metrics_specs, rest_of_metrics_specs = metrics_specs.split(is_customer_metrics)


@multi_asset(specs=[customer_metrics_specs[0]])
def run_customer_metrics() -> MaterializeResult:
    run_id = metrics_airflow_instance.trigger_dag("customer_metrics")
    metrics_airflow_instance.wait_for_run_completion("customer_metrics", run_id)
    if metrics_airflow_instance.get_run_state("customer_metrics", run_id) == "success":
        return MaterializeResult(asset_key=customer_metrics_specs[0].key)
    else:
        raise Exception("Dag run failed.")


warehouse_sensor = build_airflow_polling_sensor(
    mapped_assets=warehouse_specs,
    airflow_instance=warehouse_airflow_instance,
)
metrics_sensor = build_airflow_polling_sensor(
    mapped_assets=metrics_specs,
    airflow_instance=metrics_airflow_instance,
)

automation_sensor = AutomationConditionSensorDefinition(
    name="automation_sensor",
    target="*",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=1,
)

defs = Definitions(
    assets=[run_customer_metrics, *warehouse_specs, *rest_of_metrics_specs],
    sensors=[warehouse_sensor, metrics_sensor, automation_sensor],
)
