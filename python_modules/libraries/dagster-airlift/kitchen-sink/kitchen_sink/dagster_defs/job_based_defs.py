from dagster import Definitions
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_airlift.core import assets_with_task_mappings
from dagster_airlift.core.load_defs import build_job_based_airflow_defs

from kitchen_sink.airflow_instance import local_airflow_instance


def build_job_based_defs() -> Definitions:
    @asset(key="print_asset")
    def print_asset(context: AssetExecutionContext) -> None:
        context.add_output_metadata({"foo": "bar"})

    @asset(key="another_print_asset")
    def another_print_asset(context: AssetExecutionContext) -> None:
        context.add_output_metadata({"foo": "baz"})

    return build_job_based_airflow_defs(
        airflow_instance=local_airflow_instance(),
        mapped_defs=Definitions(
            assets=[
                *assets_with_task_mappings(
                    dag_id="deferred_events_dag",
                    task_mappings={
                        "print_task": [print_asset],
                        "downstream_print_task": [another_print_asset],
                    },
                ),
            ]
        ),
    )


defs = build_job_based_defs()
