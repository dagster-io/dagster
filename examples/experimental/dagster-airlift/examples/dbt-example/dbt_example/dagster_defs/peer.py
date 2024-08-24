from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    sync_build_defs_from_airflow_instance,
)

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = sync_build_defs_from_airflow_instance(airflow_instance=airflow_instance)
