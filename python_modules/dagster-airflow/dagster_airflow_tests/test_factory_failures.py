import os
import uuid

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import (
    make_airflow_dag_containerized_for_handle,
    make_airflow_dag_for_handle,
    make_airflow_dag_kubernetized_for_handle,
)
from dagster_airflow.test_fixtures import execute_tasks_in_dag, get_dagster_docker_image

from dagster import ExecutionTargetHandle
from dagster.utils import load_yaml_from_glob_list, script_relative_path

ENVIRONMENTS_PATH = script_relative_path(
    os.path.join(
        '..',
        '..',
        '..',
        '.buildkite',
        'images',
        'docker',
        'test_project',
        'test_pipelines',
        'environments',
    )
)


def test_error_dag_python():
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env_filesystem.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = str(uuid.uuid4())
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_for_handle(handle, pipeline_name, environment_dict)

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)


def test_error_dag_containerized():
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env_s3.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = str(uuid.uuid4())
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_containerized_for_handle(
        handle, pipeline_name, get_dagster_docker_image(), environment_dict
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)


def test_error_dag_k8s():
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env_s3.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = str(uuid.uuid4())
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_kubernetized_for_handle(
        handle=handle,
        pipeline_name=pipeline_name,
        image=get_dagster_docker_image(),
        namespace='default',
        environment_dict=environment_dict,
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)
