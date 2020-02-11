# pylint: disable=unused-import
import os
import uuid

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import make_airflow_dag_containerized_for_handle
from dagster_airflow.test_fixtures import (
    dagster_airflow_docker_operator_pipeline,
    execute_tasks_in_dag,
)
from dagster_airflow_tests.conftest import dagster_docker_image, environments_path
from dagster_airflow_tests.marks import nettest

from dagster import ExecutionTargetHandle
from dagster.core.utils import make_new_run_id
from dagster.utils import load_yaml_from_glob_list

from .utils import validate_pipeline_execution, validate_skip_pipeline_execution


def test_fs_storage_no_explicit_base_dir(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem_no_explicit_base_dir.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


def test_fs_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@nettest
def test_s3_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_s3.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


@nettest
def test_gcs_storage(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline_gcs'
    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_gcs.yaml'),
        ],
        image=dagster_docker_image,
    )
    validate_pipeline_execution(results)


def test_skip_operator(
    dagster_airflow_docker_operator_pipeline, dagster_docker_image, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'optional_outputs'

    results = dagster_airflow_docker_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name),
        environment_yaml=[os.path.join(environments_path, 'env_filesystem.yaml')],
        op_kwargs={'host_tmp_dir': '/tmp'},
        image=dagster_docker_image,
    )
    validate_skip_pipeline_execution(results)


def test_error_dag_containerized(
    dagster_docker_image, environments_path
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(environments_path, 'env_s3.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = make_new_run_id()
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_containerized_for_handle(
        handle, pipeline_name, dagster_docker_image, environment_dict
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)
