from dagster import AssetSpec, Definitions
from dagster_airlift.core import assets_with_task_mappings, build_defs_from_airflow_instance

from kitchen_sink.airflow_instance import local_airflow_instance

defs = build_defs_from_airflow_instance(
    airflow_instance=local_airflow_instance(),
    defs=Definitions(
        assets=assets_with_task_mappings(
            dag_id="dag_second_code_location",
            task_mappings={
                "task": [AssetSpec(key="dag_second_code_location__asset")],
            },
        ),
    ),
    dag_selector_fn=lambda dag_info: dag_info.dag_id == "dag_second_code_location",
)
