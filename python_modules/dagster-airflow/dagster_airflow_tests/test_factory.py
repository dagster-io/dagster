from __future__ import unicode_literals

import os
import uuid

from airflow.exceptions import AirflowSkipException
from dagster_airflow.factory import AIRFLOW_MAX_DAG_NAME_LEN, _rename_for_airflow
from dagster_airflow.test_fixtures import (  # pylint: disable=unused-import
    dagster_airflow_docker_operator_pipeline,
    dagster_airflow_k8s_operator_pipeline,
    dagster_airflow_python_operator_pipeline,
)
from dagster_airflow_tests.marks import nettest

from dagster import ExecutionTargetHandle
from dagster.core.events.log import DagsterEventRecord
from dagster.utils import script_relative_path

AIRFLOW_DEMO_EVENTS = {
    ('ENGINE_EVENT', None),
    ('STEP_START', 'multiply_the_word.compute'),
    ('STEP_INPUT', 'multiply_the_word.compute'),
    ('STEP_OUTPUT', 'multiply_the_word.compute'),
    ('OBJECT_STORE_OPERATION', 'multiply_the_word.compute'),
    ('STEP_SUCCESS', 'multiply_the_word.compute'),
    ('STEP_START', 'count_letters.compute'),
    ('OBJECT_STORE_OPERATION', 'count_letters.compute'),
    ('STEP_INPUT', 'count_letters.compute'),
    ('STEP_OUTPUT', 'count_letters.compute'),
    ('STEP_SUCCESS', 'count_letters.compute'),
}

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


def validate_pipeline_execution(pipeline_exc_result):
    seen_events = set()
    for result in pipeline_exc_result.values():
        for event in result:
            if isinstance(event, DagsterEventRecord):
                seen_events.add((event.dagster_event.event_type_value, event.step_key))
            else:
                seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == AIRFLOW_DEMO_EVENTS


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


class TestExecuteDagContainerizedFilesystemStorageNoExplicitBaseDir(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_filesystem_no_explicit_base_dir.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_docker_operator_pipeline)


@nettest
class TestExecuteDagContainerizedS3Storage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_docker_operator_pipeline)


@nettest
class TestExecuteDagContainerizedGCSStorage(object):
    pipeline_name = 'demo_pipeline_gcs'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_gcs.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_docker_operator_pipeline)


class TestExecuteDagContainerizedFilesystemStorage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [
        os.path.join(ENVIRONMENTS_PATH, 'env.yaml'),
        os.path.join(ENVIRONMENTS_PATH, 'env_filesystem.yaml'),
    ]
    run_id = str(uuid.uuid4())
    op_kwargs = {'host_tmp_dir': '/tmp'}

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_docker_operator_pipeline)


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


def validate_skip_pipeline_execution(result):
    expected_airflow_task_states = {
        ('foo', False),
        ('first_consumer', False),
        ('second_consumer', True),
        ('third_consumer', True),
    }

    seen = {(ti.task_id, isinstance(value, AirflowSkipException)) for ti, value in result.items()}
    assert seen == expected_airflow_task_states


class TestExecuteSkipsPythonOperator(object):
    pipeline_name = 'optional_outputs'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [os.path.join(ENVIRONMENTS_PATH, 'env_filesystem.yaml')]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_skip_pipeline_execution(dagster_airflow_python_operator_pipeline)


class TestExecuteSkipsContainerized(object):
    pipeline_name = 'optional_outputs'
    handle = ExecutionTargetHandle.for_pipeline_module('test_pipelines', pipeline_name)
    environment_yaml = [os.path.join(ENVIRONMENTS_PATH, 'env_filesystem.yaml')]
    run_id = str(uuid.uuid4())
    op_kwargs = {'host_tmp_dir': '/tmp'}

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_skip_pipeline_execution(dagster_airflow_docker_operator_pipeline)
