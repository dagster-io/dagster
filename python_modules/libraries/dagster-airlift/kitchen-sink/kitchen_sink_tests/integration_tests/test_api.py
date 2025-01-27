import requests
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from kitchen_sink.airflow_instance import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
)
from pytest_mock import MockFixture


def test_configure_dag_list_limit(airflow_instance: None, mocker: MockFixture) -> None:
    """Test that batch instance logic correctly retrieves all dags when over batch limit."""
    spy = mocker.spy(requests.Session, "get")
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
        ),
        name=AIRFLOW_INSTANCE_NAME,
        # Set low list limit, force batched retrieval.
        dag_list_limit=1,
    )
    assert len(af_instance.list_dags()) == 16
    # 16 with actual results, 1 with no results
    assert spy.call_count == 17
