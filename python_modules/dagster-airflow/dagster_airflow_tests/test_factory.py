from __future__ import unicode_literals

import datetime
import uuid

from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path

# pylint: disable=unused-import
from dagster_airflow.test_fixtures import (
    dagster_airflow_docker_operator_pipeline,
    dagster_airflow_python_operator_pipeline,
)
from dagster_airflow.factory import _rename_for_airflow, AIRFLOW_MAX_DAG_NAME_LEN

from dagster_airflow_tests.conftest import IMAGE
from dagster_airflow_tests.marks import nettest


AIRFLOW_DEMO_EVENTS = {
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
    execution_date = datetime.datetime.utcnow()

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
    execution_date = datetime.datetime.utcnow()

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
    execution_date = datetime.datetime.utcnow()
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
    execution_date = datetime.datetime.utcnow()
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


class TestExecuteSkipsPythonOperator(object):
    pipeline_name = 'optional_outputs'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [script_relative_path('test_project/env_filesystem.yaml')]
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        expected_airflow_task_states = {
            ('foo', None),
            ('first_consumer', None),
            ('second_consumer', 'skipped'),
            ('third_consumer', 'skipped'),
        }

        seen = {
            (ti.task_id, ti.current_state())
            for ti in dagster_airflow_python_operator_pipeline.keys()
        }
        assert seen == expected_airflow_task_states


class TestExecuteSkipsContainerized(object):
    pipeline_name = 'optional_outputs'
    handle = ExecutionTargetHandle.for_pipeline_module(
        'dagster_airflow_tests.test_project.dagster_airflow_demo', pipeline_name
    )
    environment_yaml = [script_relative_path('test_project/env_filesystem.yaml')]
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()
    op_kwargs = {'host_tmp_dir': '/tmp'}
    image = IMAGE

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        expected_airflow_task_states = {
            ('foo', None),
            ('first_consumer', None),
            ('second_consumer', 'skipped'),
            ('third_consumer', 'skipped'),
        }

        seen = {
            (ti.task_id, ti.current_state())
            for ti in dagster_airflow_docker_operator_pipeline.keys()
        }
        assert seen == expected_airflow_task_states
