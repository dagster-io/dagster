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
    dag_defs,
    load_airflow_dag_asset_specs,
    task_defs,
)
from dagster_airlift.core.multiple_tasks import targeted_by_multiple_tasks

from kitchen_sink.airflow_instance import local_airflow_instance
from kitchen_sink.dagster_defs.retries_configured import just_fails, succeeds_on_final_retry


def make_print_asset(key: str) -> AssetsDefinition:
    @asset(key=key)
    def print_asset() -> None:
        # ruff: noqa: T201
        print("Hello, world!")

    return print_asset


@asset(description="Asset one is materialized by multiple airflow tasks")
def asset_one() -> None:
    # ruff: noqa: T201
    print("Materialized asset one")


@asset(description="Asset two is materialized by an overridden dag")
def asset_two() -> None:
    print("Materialized asset two")


@asset(description="Materialized by overridden_dag_custom_callback")
def asset_overridden_dag_custom_callback() -> None:
    print("Materialized by overridden_dag_custom_callback")


# Assets within multi_job_assets_dag
@asset
def multi_job__a() -> None:
    print("Materialized a")


@asset(deps=[multi_job__a])
def multi_job__b() -> None:
    print("Materialized b")


@asset(deps=[multi_job__a])
def multi_job__c() -> None:
    print("Materialized c")


job1 = define_asset_job("job1", [multi_job__a])
job2 = define_asset_job("job2", [multi_job__b, multi_job__c])


# Partitioned assets for migrated_daily_interval_dag
@asset(
    partitions_def=DailyPartitionsDefinition(
        start_date=get_current_datetime_midnight() - timedelta(days=2)
    )
)
def migrated_daily_interval_dag__partitioned() -> None:
    print("Materialized daily_interval_dag__partitioned")


def build_mapped_defs() -> Definitions:
    return build_defs_from_airflow_instance(
        airflow_instance=local_airflow_instance(),
        dag_selector_fn=lambda dag: not dag.dag_id.startswith("unmapped"),
        defs=Definitions.merge(
            dag_defs(
                "print_dag",
                task_defs("print_task", Definitions(assets=[make_print_asset("print_asset")])),
                task_defs(
                    "downstream_print_task",
                    Definitions(assets=[make_print_asset("another_print_asset")]),
                ),
            ),
            targeted_by_multiple_tasks(
                Definitions([asset_one]),
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "asset_one_weekly"},
                    {"dag_id": "daily_dag", "task_id": "asset_one_daily"},
                ],
            ),
            Definitions(assets=assets_with_dag_mappings({"overridden_dag": [asset_two]})),
            dag_defs(
                "affected_dag",
                task_defs(
                    "print_task",
                    Definitions(assets=[make_print_asset("affected_dag__print_asset")]),
                ),
                task_defs(
                    "downstream_print_task",
                    Definitions(assets=[make_print_asset("affected_dag__another_print_asset")]),
                ),
            ),
            dag_defs(
                "unaffected_dag",
                task_defs(
                    "print_task",
                    Definitions(assets=[make_print_asset("unaffected_dag__print_asset")]),
                ),
                task_defs(
                    "downstream_print_task",
                    Definitions(assets=[make_print_asset("unaffected_dag__another_print_asset")]),
                ),
            ),
            Definitions(
                assets=assets_with_task_mappings(
                    dag_id="daily_interval_dag",
                    task_mappings={
                        "task": [
                            AssetSpec(
                                key="daily_interval_dag__partitioned",
                                partitions_def=DailyPartitionsDefinition(
                                    start_date=get_current_datetime_midnight()
                                ),
                            )
                        ],
                    },
                ),
            ),
            Definitions(
                assets_with_dag_mappings(
                    {"overridden_dag_custom_callback": [asset_overridden_dag_custom_callback]}
                )
            ),
            Definitions(
                assets_with_task_mappings(
                    dag_id="multi_job_assets_dag",
                    task_mappings={"print_task": [multi_job__a, multi_job__b, multi_job__c]},
                ),
                jobs=[job1, job2],
            ),
            Definitions(
                assets=assets_with_task_mappings(
                    dag_id="migrated_daily_interval_dag",
                    task_mappings={"my_task": [migrated_daily_interval_dag__partitioned]},
                ),
            ),
            Definitions(
                assets=assets_with_task_mappings(
                    dag_id="migrated_asset_has_retries",
                    task_mappings={"my_task": [succeeds_on_final_retry]},
                )
            ),
            Definitions(
                assets=assets_with_task_mappings(
                    dag_id="migrated_asset_has_retries_not_step_failure",
                    task_mappings={"my_task": [just_fails]},
                )
            ),
        ),
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
