import subprocess

import requests
from dagster_airlift.core import AirflowBasicAuthBackend, AirflowInstance
from dagster_airlift.in_airflow.gql_queries import VERIFICATION_QUERY


def test_load_upstream(upstream_airflow: subprocess.Popen) -> None:
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url="http://localhost:8081",
            username="admin",
            password="admin",
        ),
        name="test",
    )
    assert len(af_instance.list_dags()) == 1


def test_load_downstream(downstream_airflow: subprocess.Popen) -> None:
    af_instance = AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url="http://localhost:8082",
            username="admin",
            password="admin",
        ),
        name="test",
    )
    assert len(af_instance.list_dags()) == 1


def test_load_dagster(dagster_dev: subprocess.Popen) -> None:
    response = requests.post(
        # Timeout in seconds
        "http://localhost:3000/graphql",
        json={"query": VERIFICATION_QUERY},
        timeout=3,
    )
    assert response.status_code == 200
