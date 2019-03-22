import os

import pytest

from airflow.exceptions import AirflowException

from dagster_airflow.dagster_plugin import DagsterOperator


def test_init_modified_docker_operator():
    DagsterOperator(
        image='dagster-airflow-demo',
        api_version='auto',
        task_id='nonce',
        config='',
        pipeline_name='',
    )


def test_modified_docker_operator_bad_docker_conn():
    operator = DagsterOperator(
        image='dagster-airflow-demo',
        api_version='auto',
        task_id='nonce',
        docker_conn_id='foo_conn',
        command='--help',
        config='',
        pipeline_name='',
    )

    with pytest.raises(AirflowException, match='The conn_id `foo_conn` isn\'t defined'):
        operator.execute({})


def test_modified_docker_operator_env():
    operator = DagsterOperator(
        image='dagster-airflow-demo',
        api_version='auto',
        task_id='nonce',
        command='--help',
        config='',
        pipeline_name='',
    )
    with pytest.raises(AirflowException, match='Unhandled error type'):
        operator.execute({})


def test_modified_docker_operator_bad_command():
    operator = DagsterOperator(
        image='dagster-airflow-demo',
        api_version='auto',
        task_id='nonce',
        command='gargle bargle',
        config='',
        pipeline_name='',
    )
    with pytest.raises(AirflowException, match='\'StatusCode\': 2}'):
        operator.execute({})


# This is an artifact of the way that Circle sets up the remote Docker environment
@pytest.mark.skip_on_circle
def test_modified_docker_operator_url():
    try:
        docker_host = os.getenv('DOCKER_HOST')
        docker_tls_verify = os.getenv('DOCKER_TLS_VERIFY')
        docker_cert_path = os.getenv('DOCKER_CERT_PATH')

        os.environ['DOCKER_HOST'] = 'gargle'
        os.environ['DOCKER_TLS_VERIFY'] = 'bargle'
        os.environ['DOCKER_CERT_PATH'] = 'farfle'

        operator = DagsterOperator(
            image='dagster-airflow-demo',
            api_version='auto',
            task_id='nonce',
            docker_url=docker_host or 'unix:///var/run/docker.sock',
            tls_hostname=docker_host if docker_tls_verify else False,
            tls_ca_cert=docker_cert_path,
            command='--help',
            config='',
            pipeline_name='',
        )

        with pytest.raises(AirflowException, match='Unhandled error type'):
            operator.execute({})

    finally:
        if docker_host is not None:
            os.environ['DOCKER_HOST'] = docker_host
        else:
            del os.environ['DOCKER_HOST']

        if docker_tls_verify is not None:
            os.environ['DOCKER_TLS_VERIFY'] = docker_tls_verify
        else:
            del os.environ['DOCKER_TLS_VERIFY']

        if docker_cert_path is not None:
            os.environ['DOCKER_CERT_PATH'] = docker_cert_path or ''
        else:
            del os.environ['DOCKER_CERT_PATH']
