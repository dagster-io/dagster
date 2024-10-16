from datetime import timedelta

from dagster import Definitions, asset, define_asset_job
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._time import get_current_datetime_midnight
from dagster_airlift.core import (
    assets_with_dag_mappings,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)
from dagster_airlift.core.multiple_tasks import targeted_by_multiple_tasks

from .airflow_instance import local_airflow_instance


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
        ),
    )


defs = build_mapped_defs()
