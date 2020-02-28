from __future__ import unicode_literals

import os

import pytest
from airflow.exceptions import AirflowException
from airflow.utils import timezone
from dagster_airflow.factory import (
    AIRFLOW_MAX_DAG_NAME_LEN,
    _rename_for_airflow,
    make_airflow_dag_for_handle,
)
from dagster_airflow.test_fixtures import (  # pylint: disable=unused-import
    dagster_airflow_python_operator_pipeline,
    execute_tasks_in_dag,
)
from dagster_airflow_tests.conftest import environments_path  # pylint: disable=unused-import
from dagster_airflow_tests.marks import nettest

from dagster import ExecutionTargetHandle
from dagster.core.utils import make_new_run_id
from dagster.utils import load_yaml_from_glob_list

from .utils import validate_pipeline_execution, validate_skip_pipeline_execution


def test_fs_storage_no_explicit_base_dir(
    dagster_airflow_python_operator_pipeline, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_python_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem_no_explicit_base_dir.yaml'),
        ],
    )
    validate_pipeline_execution(results)


def test_fs_storage(
    dagster_airflow_python_operator_pipeline, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_python_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_filesystem.yaml'),
        ],
    )
    validate_pipeline_execution(results)


@nettest
def test_s3_storage(
    dagster_airflow_python_operator_pipeline, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline'
    results = dagster_airflow_python_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_s3.yaml'),
        ],
    )
    validate_pipeline_execution(results)


@nettest
def test_gcs_storage(
    dagster_airflow_python_operator_pipeline, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_pipeline_gcs'
    results = dagster_airflow_python_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[
            os.path.join(environments_path, 'env.yaml'),
            os.path.join(environments_path, 'env_gcs.yaml'),
        ],
    )
    validate_pipeline_execution(results)


def test_skip_operator(
    dagster_airflow_python_operator_pipeline, environments_path,
):  # pylint: disable=redefined-outer-name
    pipeline_name = 'optional_outputs'
    results = dagster_airflow_python_operator_pipeline(
        pipeline_name=pipeline_name,
        handle=ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name),
        environment_yaml=[os.path.join(environments_path, 'env_filesystem.yaml')],
    )
    validate_skip_pipeline_execution(results)


def test_rename_for_airflow():
    pairs = [
        ('foo', 'foo'),
        ('this-is-valid', 'this-is-valid'),
        (
            'a' * AIRFLOW_MAX_DAG_NAME_LEN + 'very long strings are disallowed',
            'a' * AIRFLOW_MAX_DAG_NAME_LEN,
        ),
        ('a name with illegal spaces', 'a_name_with_illegal_spaces'),
        ('a#name$with@special*chars!!!', 'a_name_with_special_chars___'),
    ]

    for before, after in pairs:
        assert after == _rename_for_airflow(before)


def test_error_dag_python(environments_path):  # pylint: disable=redefined-outer-name
    pipeline_name = 'demo_error_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines.repo', pipeline_name)
    environment_yaml = [
        os.path.join(environments_path, 'env_filesystem.yaml'),
    ]
    environment_dict = load_yaml_from_glob_list(environment_yaml)
    execution_date = timezone.utcnow()

    dag, tasks = make_airflow_dag_for_handle(handle, pipeline_name, environment_dict)

    with pytest.raises(AirflowException) as exc_info:
        execute_tasks_in_dag(dag, tasks, run_id=make_new_run_id(), execution_date=execution_date)

    assert 'Exception: Unusual error' in str(exc_info.value)
