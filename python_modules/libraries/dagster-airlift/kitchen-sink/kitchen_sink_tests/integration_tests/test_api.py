from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from kitchen_sink.airflow_instance import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
)


def test_configure_dag_list_limit(airflow_instance: None) -> None:
    """Test that batch instance logic correctly retrieves all dags when over batch limit."""
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
        # Set low list limit, force batched retrieval.
        dag_list_limit=1,
    )
    assert len(af_instance.list_dags()) == 16
