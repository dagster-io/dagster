from dagster import Definitions, asset
from dagster._core.definitions.assets import AssetsDefinition
from dagster_airlift.core import (
    assets_with_dag_mappings,
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
                assets_with_dag_mappings(
                    {"overridden_dag_custom_callback": [asset_overridden_dag_custom_callback]}
                )
            ),
        ),
    )


defs = build_mapped_defs()
