from __future__ import unicode_literals

import datetime
import json
import re
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
from dagster_airflow_tests.test_project.dagster_airflow_demo import define_demo_execution_pipeline


class TestExecuteDagPythonFilesystemStorage(object):
    handle = ExecutionTargetHandle.for_pipeline_fn(define_demo_execution_pipeline)
    pipeline_name = 'demo_pipeline'
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_filesystem.yaml'),
    ]
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        expected_results = {
            'multiply_the_word': '"barbar"',
            'count_letters': '{"b": 2, "a": 2, "r": 2}',
        }
        for result in dagster_airflow_python_operator_pipeline:
            assert 'data' in result
            assert 'executePlan' in result['data']
            assert '__typename' in result['data']['executePlan']
            assert result['data']['executePlan']['__typename'] == 'ExecutePlanSuccess'
            result = list(
                filter(
                    lambda x: x['__typename'] == 'ExecutionStepOutputEvent',
                    result['data']['executePlan']['stepEvents'],
                )
            )[0]
            if result['step']['kind'] == 'INPUT_THUNK':
                continue
            # This ugly beast is to deal with cross-python-version differences in `valueRepr` --
            # in py2 we'll get 'u"barbar"', in py3 we'll get '"barbar"', etc.
            assert json.loads(
                re.sub(
                    '{u\'', '{\'', re.sub(' u\'', ' \'', re.sub('^u\'', '\'', result['valueRepr']))
                ).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solidHandleID']].replace('\'', '"'))


class TestExecuteDagPythonS3Storage(object):
    handle = ExecutionTargetHandle.for_pipeline_fn(define_demo_execution_pipeline)
    pipeline_name = 'demo_pipeline'
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()

    # pylint: disable=redefined-outer-name
    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        expected_results = {
            'multiply_the_word': '"barbar"',
            'count_letters': '{"b": 2, "a": 2, "r": 2}',
        }
        for result in dagster_airflow_python_operator_pipeline:
            assert 'data' in result
            assert 'executePlan' in result['data']
            assert '__typename' in result['data']['executePlan']
            assert result['data']['executePlan']['__typename'] == 'ExecutePlanSuccess'
            result = list(
                filter(
                    lambda x: x['__typename'] == 'ExecutionStepOutputEvent',
                    result['data']['executePlan']['stepEvents'],
                )
            )[0]
            if result['step']['kind'] == 'INPUT_THUNK':
                continue
            # This ugly beast is to deal with cross-python-version differences in `valueRepr` --
            # in py2 we'll get 'u"barbar"', in py3 we'll get '"barbar"', etc.
            assert json.loads(
                # pylint: disable=anomalous-backslash-in-string
                re.sub(
                    r'\{u\'',
                    '{\'',
                    re.sub(' u\'', ' \'', re.sub('^u\'', '\'', result['valueRepr'])),
                ).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solidHandleID']].replace('\'', '"'))


@nettest
class TestExecuteDagContainerizedS3Storage(object):
    handle = ExecutionTargetHandle.for_pipeline_fn(define_demo_execution_pipeline)
    pipeline_name = 'demo_pipeline'
    environment_yaml = [
        script_relative_path('test_project/env.yaml'),
        script_relative_path('test_project/env_s3.yaml'),
    ]
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()
    image = IMAGE

    # pylint: disable=redefined-outer-name
    def test_execute_dag_containerized(self, dagster_airflow_docker_operator_pipeline):
        expected_results = {
            'multiply_the_word': '"barbar"',
            'count_letters': '{"b": 2, "a": 2, "r": 2}',
        }
        for result in dagster_airflow_docker_operator_pipeline:
            assert 'data' in result
            assert 'executePlan' in result['data']
            assert '__typename' in result['data']['executePlan']
            assert result['data']['executePlan']['__typename'] == 'ExecutePlanSuccess'
            result = list(
                filter(
                    lambda x: x['__typename'] == 'ExecutionStepOutputEvent',
                    result['data']['executePlan']['stepEvents'],
                )
            )[0]
            if result['step']['kind'] == 'INPUT_THUNK':
                continue
            assert json.loads(
                # pylint: disable=anomalous-backslash-in-string
                re.sub(
                    r'\{u\'',
                    '{\'',
                    re.sub(' u\'', ' \'', re.sub('^u\'', '\'', result['valueRepr'])),
                ).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solidHandleID']].replace('\'', '"'))


class TestExecuteDagContainerizedFilesystemStorage(object):
    handle = ExecutionTargetHandle.for_pipeline_fn(define_demo_execution_pipeline)
    pipeline_name = 'demo_pipeline'
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
        expected_results = {
            'multiply_the_word': '"barbar"',
            'count_letters': '{"b": 2, "a": 2, "r": 2}',
        }
        for result in dagster_airflow_docker_operator_pipeline:
            assert 'data' in result
            assert 'executePlan' in result['data']
            assert '__typename' in result['data']['executePlan']
            assert result['data']['executePlan']['__typename'] == 'ExecutePlanSuccess'
            result = list(
                filter(
                    lambda x: x['__typename'] == 'ExecutionStepOutputEvent',
                    result['data']['executePlan']['stepEvents'],
                )
            )[0]
            if result['step']['kind'] == 'INPUT_THUNK':
                continue
            assert json.loads(
                re.sub(
                    '{u\'', '{\'', re.sub(' u\'', ' \'', re.sub('^u\'', '\'', result['valueRepr']))
                ).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solidHandleID']].replace('\'', '"'))


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
