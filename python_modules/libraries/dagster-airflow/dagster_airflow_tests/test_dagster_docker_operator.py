import os

import pytest
from airflow.exceptions import AirflowException
from dagster_airflow.operators.docker_operator import DagsterDockerOperator
from dagster_graphql.client.mutations import DagsterGraphQLClientError

from .conftest import dagster_docker_image  # pylint: disable=unused-import


def test_init_modified_docker_operator(
    dagster_docker_image,
):  # pylint: disable=redefined-outer-name
    DagsterDockerOperator(
        image=dagster_docker_image,
        api_version='auto',
        task_id='nonce',
        environment_dict={'storage': {'filesystem': {}}},
        pipeline_name='',
        mode='default',
    )


def test_modified_docker_operator_bad_docker_conn(
    dagster_docker_image,
):  # pylint: disable=redefined-outer-name
    operator = DagsterDockerOperator(
        image=dagster_docker_image,
        api_version='auto',
        task_id='nonce',
        docker_conn_id='foo_conn',
        command='dagster-graphql --help',
        environment_dict={'storage': {'filesystem': {}}},
        pipeline_name='',
        mode='default',
    )

    with pytest.raises(AirflowException, match='The conn_id `foo_conn` isn\'t defined'):
        operator.execute({})


def test_modified_docker_operator_env(dagster_docker_image):  # pylint: disable=redefined-outer-name
    operator = DagsterDockerOperator(
        image=dagster_docker_image,
        api_version='auto',
        task_id='nonce',
        command='dagster-graphql --help',
        environment_dict={'storage': {'filesystem': {}}},
        pipeline_name='',
        mode='default',
    )
    with pytest.raises(DagsterGraphQLClientError, match='Unhandled error type'):
        operator.execute({})


def test_modified_docker_operator_bad_command(
    dagster_docker_image,
):  # pylint: disable=redefined-outer-name
    operator = DagsterDockerOperator(
        image=dagster_docker_image,
        api_version='auto',
        task_id='nonce',
        command='dagster-graphql gargle bargle',
        environment_dict={'storage': {'filesystem': {}}},
        pipeline_name='',
        mode='default',
    )
    with pytest.raises(AirflowException, match='\'StatusCode\': 2'):
        operator.execute({})


def test_modified_docker_operator_url(dagster_docker_image):  # pylint: disable=redefined-outer-name
    try:
        docker_host = os.getenv('DOCKER_HOST')
        docker_tls_verify = os.getenv('DOCKER_TLS_VERIFY')
        docker_cert_path = os.getenv('DOCKER_CERT_PATH')

        os.environ['DOCKER_HOST'] = 'gargle'
        os.environ['DOCKER_TLS_VERIFY'] = 'bargle'
        os.environ['DOCKER_CERT_PATH'] = 'farfle'

        operator = DagsterDockerOperator(
            image=dagster_docker_image,
            api_version='auto',
            task_id='nonce',
            docker_url=docker_host or 'unix:///var/run/docker.sock',
            tls_hostname=docker_host if docker_tls_verify else False,
            tls_ca_cert=docker_cert_path,
            command='dagster-graphql --help',
            environment_dict={'storage': {'filesystem': {}}},
            pipeline_name='',
            mode='default',
        )

        with pytest.raises(DagsterGraphQLClientError, match='Unhandled error type'):
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
