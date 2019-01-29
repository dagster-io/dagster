import pytest

from airflow.exceptions import AirflowException

from dagster_airflow.dagster_plugin import ModifiedDockerOperator


def test_init_modified_docker_operator():
    ModifiedDockerOperator(image='dagster-airflow-demo', api_version='auto', task_id='nonce')


def test_modified_docker_operator_bad_docker_conn():
    operator = ModifiedDockerOperator(
        image='dagster-airflow-demo', api_version='auto', task_id='nonce', docker_conn_id='foo_conn'
    )

    with pytest.raises(AirflowException, match='The conn_id `foo_conn` isn\'t defined'):
        operator.execute({})
