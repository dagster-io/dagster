from __future__ import unicode_literals

import os
import uuid

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
from dagster_airflow_tests.marks import nettest

from dagster import ExecutionTargetHandle
from dagster.utils import load_yaml_from_glob_list, script_relative_path

from .utils import validate_pipeline_execution, validate_skip_pipeline_execution

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


class TestExecuteDagPythonFilesystemStorageNoExplicitBaseDir(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_filesystem_no_explicit_base_dir.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_python_operator_pipeline)


class TestExecuteDagPythonFilesystemStorage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_filesystem.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_python_operator_pipeline)


@nettest
class TestExecuteDagPythonS3Storage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_python_operator_pipeline)


@nettest
class TestExecuteDagPythonGCSStorage(object):
    pipeline_name = 'demo_pipeline_gcs'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_gcs.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_python_operator_pipeline)


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


class TestExecuteSkipsPythonOperator(object):
    pipeline_name = 'optional_outputs'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [os.path.join(ENVIRONMENTS_PATH, 'env_filesystem.yaml')]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_skip_pipeline_execution(dagster_airflow_python_operator_pipeline)


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
