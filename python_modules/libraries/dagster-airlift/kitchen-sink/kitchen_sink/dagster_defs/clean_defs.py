from dagster import Definitions, multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_airlift.core import build_defs_from_airflow_instance, load_airflow_dag_asset_specs

from kitchen_sink.airflow_instance import local_airflow_instance


def build_mapped_defs() -> Definitions:
    return build_defs_from_airflow_instance(
        airflow_instance=local_airflow_instance(),
        dag_selector_fn=lambda dag: not dag.dag_id.startswith("unmapped"),
        sensor_minimum_interval_seconds=1,
    )


unmapped_specs = load_airflow_dag_asset_specs(
    airflow_instance=local_airflow_instance(),
    dag_selector_fn=lambda dag: dag.dag_id.startswith("unmapped"),
)


@multi_asset(specs=unmapped_specs)
def materialize_dags(context: AssetExecutionContext):
    for spec in unmapped_specs:
        af_instance = local_airflow_instance()
        dag_id = spec.metadata["Dag ID"]
        dag_run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=dag_run_id)
        state = af_instance.get_run_state(dag_id=dag_id, run_id=dag_run_id)
        if state != "success":
            raise Exception(f"Failed to materialize {dag_id} with state {state}")


defs = Definitions.merge(build_mapped_defs(), Definitions([materialize_dags]))
