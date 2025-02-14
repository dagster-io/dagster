from typing import Optional

from dagster_airlift.core import AirflowBasicAuthBackend, AirflowInstance

from kitchen_sink.constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME


def local_airflow_instance(name: Optional[str] = None) -> AirflowInstance:
    return AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=name or AIRFLOW_INSTANCE_NAME,
    )
