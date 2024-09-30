from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import AirflowInstance, BasicAuthBackend
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def build_automapped_defs() -> Definitions:
    return build_full_automapped_dags_from_airflow_instance(
        airflow_instance=airflow_instance,
    )


defs = build_automapped_defs()
