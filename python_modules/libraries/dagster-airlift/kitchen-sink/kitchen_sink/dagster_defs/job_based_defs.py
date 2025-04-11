from datetime import timedelta

from dagster import Definitions, asset, define_asset_job, multi_asset
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._time import get_current_datetime_midnight
from dagster_airlift.core import (
    assets_with_dag_mappings,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
    load_airflow_dag_asset_specs,
)
from dagster_airlift.core.load_defs import build_job_based_airflow_defs
from dagster_airlift.core.multiple_tasks import targeted_by_multiple_tasks

from kitchen_sink.airflow_instance import local_airflow_instance
from kitchen_sink.dagster_defs.retries_configured import just_fails, succeeds_on_final_retry


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
