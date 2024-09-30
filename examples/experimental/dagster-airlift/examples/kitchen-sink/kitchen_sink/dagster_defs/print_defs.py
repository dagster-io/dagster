# ruff: noqa: T201
from dagster import Definitions, asset
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, dag_defs, task_defs

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


@asset
def print_asset():
    print("Hello, world!")


defs = Definitions.merge(
    dag_defs(
        "print_dag",
        task_defs("print_task", Definitions(assets=[print_asset])),
    ),
)
