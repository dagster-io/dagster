from dagster import (
    AutomationConditionSensorDefinition,
    DefaultSensorStatus,
    Definitions,
    MaterializeResult,
    multi_asset,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    build_airflow_polling_sensor,
    load_airflow_dag_asset_specs,
)
from dagster_airlift.core.utils import merge_spec_attrs, replace_spec_attrs, split_specs

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


# This would be part of library code
def get_dag_id(spec: AssetSpec) -> str:
    return spec.metadata["Dag ID"]


warehouse_specs = load_airflow_dag_asset_specs(airflow_instance=warehouse_airflow_instance)

load_customers_dag_specs = [
    spec for spec in warehouse_specs if get_dag_id(spec) == "load_customers"
]

is_customer_metrics_dag = lambda spec: get_dag_id(spec) == "customer_metrics"

metrics_specs = merge_spec_attrs(
    replace_spec_attrs(
        load_airflow_dag_asset_specs(airflow_instance=metrics_airflow_instance),
        automation_condition=AutomationCondition.eager(),
    ),
    where=is_customer_metrics_dag,
    deps=load_customers_dag_specs,
)

customer_metrics, remaining_metrics_specs = split_specs(
    metrics_specs, where=is_customer_metrics_dag
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
