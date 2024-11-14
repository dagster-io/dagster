from typing import AbstractSet

from dagster import (
    AutomationConditionSensorDefinition,
    DefaultSensorStatus,
    Definitions,
    MaterializeResult,
    multi_asset,
)
from dagster._core.definitions.asset_spec import merge_attributes
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
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


def dag_id_matches(spec, dag_ids: AbstractSet[str]) -> bool:
    return spec.metadata.get("Dag ID") in dag_ids


warehouse_specs = load_airflow_dag_asset_specs(airflow_instance=warehouse_airflow_instance)

load_customers_dag_specs = [
    spec for spec in warehouse_specs if dag_id_matches(spec, {"load_customers"})
]

is_customer_dag = lambda spec: dag_id_matches(spec, {"customer_metrics"})

metrics_specs = [
    merge_attributes(
        spec, deps=load_customers_dag_specs, automation_condition=AutomationCondition.eager()
    )
    if not is_customer_dag(spec)
    else spec
    for spec in load_airflow_dag_asset_specs(airflow_instance=metrics_airflow_instance)
]

customer_metrics, remaining_metrics_specs = (
    [spec for spec in metrics_specs if is_customer_dag(spec)],
    [spec for spec in metrics_specs if not is_customer_dag(spec)],
)


@multi_asset(specs=customer_metrics)
def run_customer_metrics() -> MaterializeResult:
    run_id = metrics_airflow_instance.trigger_dag("customer_metrics")
    metrics_airflow_instance.wait_for_run_completion("customer_metrics", run_id)
    if metrics_airflow_instance.get_run_state("customer_metrics", run_id) == "success":
        return MaterializeResult(asset_key=customer_metrics[0].key)
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
    assets=[run_customer_metrics, *remaining_metrics_specs, *warehouse_specs],
    sensors=[warehouse_sensor, metrics_sensor, automation_sensor],
)
