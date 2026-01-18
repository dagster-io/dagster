import subprocess

import requests
from airlift_federation_tutorial_tests.conftest import (
    assert_successful_dag_run,
    metrics_instance,
    warehouse_instance,
)
from dagster_airlift.in_airflow.gql_queries import VERIFICATION_QUERY


def test_load_warehouse(warehouse_airflow: subprocess.Popen) -> None:
    af_instance = warehouse_instance()
    assert len(af_instance.list_dags()) == 5
    assert_successful_dag_run(af_instance, "load_customers")


def test_load_metrics(metrics_airflow: subprocess.Popen) -> None:
    assert len(metrics_instance().list_dags()) == 5
    assert_successful_dag_run(metrics_instance(), "customer_metrics")


def test_load_dagster(dagster_dev: subprocess.Popen) -> None:
    response = requests.post(
        # Timeout in seconds
        "http://localhost:3000/graphql",
        json={"query": VERIFICATION_QUERY},
        timeout=3,
    )
    assert response.status_code == 200
