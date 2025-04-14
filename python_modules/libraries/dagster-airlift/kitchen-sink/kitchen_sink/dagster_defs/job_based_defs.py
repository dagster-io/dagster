from dagster import Definitions
from dagster._core.definitions.asset_spec import AssetSpec
from dagster_airlift.core import assets_with_task_mappings
from dagster_airlift.core.load_defs import build_job_based_airflow_defs

from kitchen_sink.airflow_instance import local_airflow_instance


def build_job_based_defs() -> Definitions:
    return build_job_based_airflow_defs(
        airflow_instance=local_airflow_instance(),
        mapped_defs=Definitions(
            assets=assets_with_task_mappings(
                dag_id="print_dag",
                task_mappings={
                    "print_task": [AssetSpec("print_asset")],
                    "downstream_print_task": [AssetSpec("another_print_asset")],
                },
            ),
        ),
    )


defs = build_job_based_defs()
