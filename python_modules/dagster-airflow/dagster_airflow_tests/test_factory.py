from __future__ import unicode_literals

import uuid

from airflow.exceptions import AirflowSkipException
from dagster_airflow.factory import AIRFLOW_MAX_DAG_NAME_LEN, _rename_for_airflow
from dagster_airflow.test_fixtures import (  # pylint: disable=unused-import
    dagster_airflow_docker_operator_pipeline,
    dagster_airflow_python_operator_pipeline,
)
from dagster_airflow_tests.conftest import IMAGE
from dagster_airflow_tests.marks import nettest

from dagster import ExecutionTargetHandle
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


def validate_pipeline_execution(pipeline_exc_result):
    seen_events = set()
    for result in pipeline_exc_result.values():
        for event in result:
            seen_events.add((event.event_type_value, event.step_key))

    assert seen_events == AIRFLOW_DEMO_EVENTS


class TestExecuteDagPythonFilesystemStorage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_filesystem.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_python_operator_pipeline)


class TestExecuteDagPythonS3Storage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_python_operator_pipeline)


@nettest
class TestExecuteDagContainerizedS3Storage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())
    image = IMAGE

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_docker_operator_pipeline)


class TestExecuteDagContainerizedFilesystemStorage(object):
    pipeline_name = 'demo_pipeline'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_filesystem.yaml'),
    ]
    run_id = str(uuid.uuid4())
    op_kwargs = {'host_tmp_dir': '/tmp'}
    image = IMAGE

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_pipeline_execution(dagster_airflow_docker_operator_pipeline)


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
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [script_relative_path('test_project/env_filesystem.yaml')]
    run_id = str(uuid.uuid4())

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        validate_skip_pipeline_execution(dagster_airflow_python_operator_pipeline)


class TestExecuteSkipsContainerized(object):
    pipeline_name = 'optional_outputs'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [script_relative_path('test_project/env_filesystem.yaml')]
    run_id = str(uuid.uuid4())
    op_kwargs = {'host_tmp_dir': '/tmp'}
    image = IMAGE

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        validate_skip_pipeline_execution(dagster_airflow_docker_operator_pipeline)
