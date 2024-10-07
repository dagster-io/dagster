from dagster import Definitions, asset
from dagster_airlift.core import build_defs_from_airflow_instance, dag_defs, task_defs
from dagster_airlift.core.multiple_tasks import targeted_by_multiple_tasks

from .airflow_instance import local_airflow_instance


@asset
def print_asset() -> None:
    # ruff: noqa: T201
    print("Hello, world!")


@asset
def another_print_asset() -> None:
    print("Hello, world!")


@asset(description="Asset one is materialized by multiple airflow tasks")
def asset_one() -> None:
    # ruff: noqa: T201
    print("Materialized asset one")


def build_mapped_defs() -> Definitions:
    return build_defs_from_airflow_instance(
        airflow_instance=local_airflow_instance(),
        defs=Definitions.merge(
            dag_defs(
                "print_dag",
                task_defs("print_task", Definitions(assets=[print_asset])),
                task_defs("downstream_print_task", Definitions(assets=[another_print_asset])),
            ),
            targeted_by_multiple_tasks(
                Definitions([asset_one]),
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "asset_one_weekly"},
                    {"dag_id": "daily_dag", "task_id": "asset_one_daily"},
                ],
            ),
        ),
    )


defs = build_mapped_defs()
