# pylint: disable=redefined-outer-name, unused-argument

import os
import sys

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import make_airflow_dag_kubernetized_for_handle
from dagster_airflow.test_fixtures import (  # pylint: disable=unused-import
    dagster_airflow_k8s_operator_pipeline,
    execute_tasks_in_dag,
)
from dagster_airflow_tests.marks import nettest, requires_k8s

from dagster import ExecutionTargetHandle
from dagster.core.utils import make_new_run_id
from dagster.utils import git_repository_root, load_yaml_from_glob_list

from .utils import validate_pipeline_execution

sys.path.append(os.path.join(git_repository_root(), 'python_modules', 'libraries', 'dagster-k8s'))
from dagster_k8s_tests.test_project import test_project_environments_path  # isort:skip


@nettest
@requires_k8s
def test_s3_storage(dagster_airflow_k8s_operator_pipeline, dagster_docker_image, cluster_provider):
    print('--- :airflow: test_kubernetes.test_s3_storage')
    _check_aws_creds_available()
    environments_path = test_project_environments_path()

    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_k8s_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_s3.yaml'),
        ],
        image=dagster_docker_image,
        op_kwargs={
            'config_file': os.environ['KUBECONFIG'],
            'env_vars': {
                'AWS_ACCESS_KEY_ID': os.environ['AWS_ACCESS_KEY_ID'],
                'AWS_SECRET_ACCESS_KEY': os.environ['AWS_SECRET_ACCESS_KEY'],
            },
        },
    )
    validate_pipeline_execution(results)


@nettest
@requires_k8s
def test_gcs_storage(
    dagster_airflow_k8s_operator_pipeline, dagster_docker_image, cluster_provider,
):
    print('--- :airflow: test_kubernetes.test_gcs_storage')

    environments_path = test_project_environments_path()

    pipeline_name = 'demo_pipeline_gcs'
    results = dagster_airflow_k8s_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_gcs.yaml'),
        ],
        image=dagster_docker_image,
        op_kwargs={'config_file': os.environ['KUBECONFIG']},
    )
    validate_pipeline_execution(results)


@requires_k8s
def test_error_dag_k8s(dagster_docker_image, cluster_provider):
    print('--- :airflow: test_kubernetes.test_error_dag_k8s')
    _check_aws_creds_available()

    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name)
    environments_path = test_project_environments_path()
    environment_yaml = [
        os.path.join(environments_path, 'env_s3.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)

    run_id = make_new_run_id()
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_kubernetized_for_handle(
        handle=handle,
        pipeline_name=pipeline_name,
        image=dagster_docker_image,
        namespace='default',
        environment_dict=environment_dict,
        op_kwargs={
            'config_file': os.environ['KUBECONFIG'],
            'env_vars': {
                'AWS_ACCESS_KEY_ID': os.environ['AWS_ACCESS_KEY_ID'],
                'AWS_SECRET_ACCESS_KEY': os.environ['AWS_SECRET_ACCESS_KEY'],
            },
        },
    )

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id, execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)


def _check_aws_creds_available():
    for expected_env_var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']:
        if expected_env_var not in os.environ:
            raise Exception(
                'Could not find %s in environment; AWS credentials AWS_ACCESS_KEY_ID and '
                'AWS_SECRET_ACCESS_KEY must be set in environment for dagster-airflow k8s tests to '
                'run, as credentials are needed to access S3 from within the Docker container '
                'running on kind.' % expected_env_var
            )
