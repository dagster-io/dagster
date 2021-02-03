import os

import pytest
from airflow.exceptions import AirflowException
from dagster import pipeline, solid
from dagster.core.execution.api import create_execution_plan
from dagster.core.snap import snapshot_from_execution_plan
from dagster.core.test_utils import instance_for_test
from dagster_airflow.factory import DagsterOperatorParameters
from dagster_airflow.operators.docker_operator import DagsterDockerOperator
from dagster_airflow_tests.marks import requires_airflow_db


@solid
def nonce_solid(_):
    return


@pipeline
def nonce_pipeline():
    return nonce_solid()


nonce_pipeline_snapshot = nonce_pipeline.get_pipeline_snapshot()

nonce_execution_plan_snapshot = snapshot_from_execution_plan(
    create_execution_plan(nonce_pipeline), nonce_pipeline.get_pipeline_snapshot_id()
)


def test_init_modified_docker_operator(dagster_docker_image):
    with instance_for_test() as instance:
        dagster_operator_parameters = DagsterOperatorParameters(
            task_id="nonce",
            run_config={"intermediate_storage": {"filesystem": {}}},
            pipeline_name="",
            mode="default",
            op_kwargs={
                "image": dagster_docker_image,
                "api_version": "auto",
            },
            pipeline_snapshot=nonce_pipeline_snapshot,
            execution_plan_snapshot=nonce_execution_plan_snapshot,
            instance_ref=instance.get_ref(),
        )
        DagsterDockerOperator(dagster_operator_parameters)


@requires_airflow_db
def test_modified_docker_operator_bad_docker_conn(dagster_docker_image):
    with instance_for_test() as instance:
        dagster_operator_parameters = DagsterOperatorParameters(
            task_id="nonce",
            run_config={"intermediate_storage": {"filesystem": {}}},
            pipeline_name="",
            mode="default",
            op_kwargs={
                "image": dagster_docker_image,
                "api_version": "auto",
                "docker_conn_id": "foo_conn",
                "command": "dagster-graphql --help",
            },
            pipeline_snapshot=nonce_pipeline_snapshot,
            execution_plan_snapshot=nonce_execution_plan_snapshot,
            instance_ref=instance.get_ref(),
        )
        operator = DagsterDockerOperator(dagster_operator_parameters)

        with pytest.raises(AirflowException, match="The conn_id `foo_conn` isn't defined"):
            operator.execute({})


def test_modified_docker_operator_env(dagster_docker_image):
    with instance_for_test() as instance:
        dagster_operator_parameters = DagsterOperatorParameters(
            task_id="nonce",
            run_config={"intermediate_storage": {"filesystem": {}}},
            pipeline_name="",
            mode="default",
            op_kwargs={
                "image": dagster_docker_image,
                "api_version": "auto",
                "command": "dagster-graphql --help",
            },
            pipeline_snapshot=nonce_pipeline_snapshot,
            execution_plan_snapshot=nonce_execution_plan_snapshot,
            instance_ref=instance.get_ref(),
        )
        operator = DagsterDockerOperator(dagster_operator_parameters)
        with pytest.raises(AirflowException, match="Could not parse response"):
            operator.execute({})


def test_modified_docker_operator_bad_command(dagster_docker_image):
    with instance_for_test() as instance:
        dagster_operator_parameters = DagsterOperatorParameters(
            task_id="nonce",
            run_config={"intermediate_storage": {"filesystem": {}}},
            pipeline_name="",
            mode="default",
            op_kwargs={
                "image": dagster_docker_image,
                "api_version": "auto",
                "command": "dagster-graphql gargle bargle",
            },
            pipeline_snapshot=nonce_pipeline_snapshot,
            execution_plan_snapshot=nonce_execution_plan_snapshot,
            instance_ref=instance.get_ref(),
        )
        operator = DagsterDockerOperator(dagster_operator_parameters)
        with pytest.raises(AirflowException, match="'StatusCode': 2"):
            operator.execute({})


def test_modified_docker_operator_url(dagster_docker_image):
    try:
        docker_host = os.getenv("DOCKER_HOST")
        docker_tls_verify = os.getenv("DOCKER_TLS_VERIFY")
        docker_cert_path = os.getenv("DOCKER_CERT_PATH")

        os.environ["DOCKER_HOST"] = "gargle"
        os.environ["DOCKER_TLS_VERIFY"] = "bargle"
        os.environ["DOCKER_CERT_PATH"] = "farfle"

        with instance_for_test() as instance:
            dagster_operator_parameters = DagsterOperatorParameters(
                task_id="nonce",
                run_config={"intermediate_storage": {"filesystem": {}}},
                pipeline_name="",
                mode="default",
                op_kwargs={
                    "image": dagster_docker_image,
                    "api_version": "auto",
                    "docker_url": docker_host or "unix:///var/run/docker.sock",
                    "tls_hostname": docker_host if docker_tls_verify else False,
                    "tls_ca_cert": docker_cert_path,
                    "command": "dagster-graphql --help",
                },
                pipeline_snapshot=nonce_pipeline_snapshot,
                execution_plan_snapshot=nonce_execution_plan_snapshot,
                instance_ref=instance.get_ref(),
            )
            operator = DagsterDockerOperator(dagster_operator_parameters)

            with pytest.raises(AirflowException, match="Could not parse response"):
                operator.execute({})

    finally:
        if docker_host is not None:
            os.environ["DOCKER_HOST"] = docker_host
        else:
            del os.environ["DOCKER_HOST"]

        if docker_tls_verify is not None:
            os.environ["DOCKER_TLS_VERIFY"] = docker_tls_verify
        else:
            del os.environ["DOCKER_TLS_VERIFY"]

        if docker_cert_path is not None:
            os.environ["DOCKER_CERT_PATH"] = docker_cert_path or ""
        else:
            del os.environ["DOCKER_CERT_PATH"]
