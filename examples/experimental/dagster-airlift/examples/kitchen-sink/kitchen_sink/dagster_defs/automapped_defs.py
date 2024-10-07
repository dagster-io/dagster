from dagster import Definitions, asset
from dagster_airlift.core import dag_defs, task_defs
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance

from .airflow_instance import local_airflow_instance


@asset
def the_print_asset() -> None:
    # ruff: noqa: T201
    print("Hello, world!")


@asset(deps=[the_print_asset])
def the_downstream_print_asset() -> None:
    # ruff: noqa: T201
    print("Hello, world!")


def build_full_automapped_defs() -> Definitions:
    return build_full_automapped_dags_from_airflow_instance(
        airflow_instance=local_airflow_instance(),
        defs=dag_defs(
            "print_dag",
            task_defs("print_task", Definitions(assets=[the_print_asset])),
            task_defs("downstream_print_task", Definitions(assets=[the_downstream_print_asset])),
        ),
    )


defs = build_full_automapped_defs()
