from __future__ import unicode_literals

import datetime
import json
import re
import uuid

from dagster.utils import script_relative_path

# pylint: unused-import
from dagster_airflow.test_fixtures import (
    dagster_airflow_docker_operator_pipeline,
    dagster_airflow_python_operator_pipeline,
)

from .conftest import IMAGE
from .marks import nettest
from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


class TestExecuteDag(object):
    pipeline = define_demo_execution_pipeline()
    config_yaml = [
        script_relative_path('test_project/env.yml'),
        script_relative_path('test_project/env_local.yml'),
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
                    '\{u\'', '{\'', re.sub(' u\'', ' \'', re.sub('^u\'', '\'', result['valueRepr']))
                ).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solid']['name']].replace('\'', '"'))


@nettest
class TestExecuteDagContainerized(object):
    pipeline = define_demo_execution_pipeline()
    config_yaml = [
        script_relative_path('test_project/env.yml'),
        script_relative_path('test_project/env_containerized.yml'),
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
                    '\{u\'', '{\'', re.sub(' u\'', ' \'', re.sub('^u\'', '\'', result['valueRepr']))
                ).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solid']['name']].replace('\'', '"'))
