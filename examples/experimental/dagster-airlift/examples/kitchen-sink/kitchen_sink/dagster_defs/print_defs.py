# ruff: noqa: T201
from dagster import Definitions, asset
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, dag_defs, task_defs
from dagster_airlift.core.multiple_tasks import targeted_by_multiple_tasks

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


@asset
def print_asset() -> None:
    print("Hello, world!")


@asset(description="Asset one is materialized by multiple airflow tasks")
def asset_one() -> None:
    print("Materialized asset one")


defs = Definitions.merge(
    dag_defs(
        "print_dag",
        task_defs("print_task", Definitions(assets=[print_asset])),
    ),
    Definitions(
        assets=[
            targeted_by_multiple_tasks(
                asset_one,
                task_handles=[
                    {"dag_id": "weekly_dag", "task_id": "asset_one_weekly"},
                    {"dag_id": "daily_dag", "task_id": "asset_one_daily"},
                ],
            )
        ]
    ),
)
