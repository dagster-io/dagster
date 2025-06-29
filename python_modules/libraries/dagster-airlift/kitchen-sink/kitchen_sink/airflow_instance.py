from typing import Optional

from dagster_airlift.core import AirflowBasicAuthBackend, AirflowInstance
from dagster_airlift.core.airflow_instance import AirflowAuthBackend, AirflowVersion
from dagster_airlift.core.token_backend import AirflowBearerTokenBackend
from dagster_airlift.test.shared_fixtures import get_jwt_token

from kitchen_sink.constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

EXPECTED_NUM_DAGS = 20


def get_backend(airflow_version: AirflowVersion) -> AirflowAuthBackend:
    if airflow_version == AirflowVersion.AIRFLOW_2:
        return AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        )
    elif airflow_version == AirflowVersion.AIRFLOW_3:
        return AirflowBearerTokenBackend(webserver_url=AIRFLOW_BASE_URL, token=get_jwt_token())
    else:
        raise ValueError(f"Unsupported Airflow version: {airflow_version}")


def local_airflow_instance(
    name: Optional[str] = None, airflow_version: AirflowVersion = AirflowVersion.AIRFLOW_2
) -> AirflowInstance:
    return AirflowInstance(
        auth_backend=get_backend(airflow_version),
        name=name or AIRFLOW_INSTANCE_NAME,
        airflow_version=airflow_version,
    )
