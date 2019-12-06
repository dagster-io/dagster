import uuid

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import (
    make_airflow_dag_containerized_for_handle,
    make_airflow_dag_for_handle,
    make_airflow_dag_kubernetized_for_handle,
)
from dagster_airflow.test_fixtures import execute_tasks_in_dag
from dagster_airflow_tests.conftest import IMAGE

from dagster import ExecutionTargetHandle
from dagster.utils import load_yaml_from_glob_list, script_relative_path


def test_error_dag_python():
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env_filesystem.yaml'),
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
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env_s3.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = str(uuid.uuid4())
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_containerized_for_handle(
        handle, pipeline_name, IMAGE, environment_dict
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)


def test_error_dag_k8s():
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env_s3.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = str(uuid.uuid4())
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_kubernetized_for_handle(
        handle=handle,
        pipeline_name=pipeline_name,
        image=IMAGE,
        namespace='default',
        environment_dict=environment_dict,
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)
