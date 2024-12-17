from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    build_defs_from_airflow_instance,
)

from perf_harness.dagster_defs.constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
)

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = build_defs_from_airflow_instance(airflow_instance=airflow_instance)
