import os
import uuid

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import make_airflow_dag_kubernetized_for_handle
from dagster_airflow.test_fixtures import (  # pylint: disable=unused-import
    dagster_airflow_k8s_operator_pipeline,
    execute_tasks_in_dag,
    get_dagster_docker_image,
)
from dagster_airflow_tests.marks import nettest

from dagster import ExecutionTargetHandle
from dagster.utils import load_yaml_from_glob_list, script_relative_path

from .utils import validate_pipeline_execution

# TODO (Nate): Will remove in follow-up diff
ENVIRONMENTS_PATH = script_relative_path(
    os.path.join(
        '..',
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


@nettest
class TestExecuteDagKubernetizedS3Storage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag_kubernetized(self, dagster_airflow_k8s_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_k8s_operator_pipeline)


@nettest
class TestExecuteDagKubernetizedGCSStorage(object):
    pipeline_name = 'demo_pipeline_gcs'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_gcs.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag_kubernetized(self, dagster_airflow_k8s_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_k8s_operator_pipeline)


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
