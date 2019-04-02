from __future__ import unicode_literals

import datetime
import json
import re
import uuid

from dagster.utils import script_relative_path

from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


class TestExecuteDag(object):
    pipeline = define_demo_execution_pipeline()
    config_yaml = [script_relative_path('test_project/env.yml')]
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()

    def test_execute_dag(self, dagster_airflow_python_operator_pipeline):
        expected_results = {
            'multiply_the_word': '\'barbar\'',
            'count_letters': '{\'b\': 2, \'a\': 2, \'r\': 2}',
        }
        for result in dagster_airflow_python_operator_pipeline:
            assert 'data' in result
            assert 'executePlan' in result['data']
            assert '__typename' in result['data']['executePlan']
            assert result['data']['executePlan']['__typename'] == 'ExecutePlanSuccess'
            result = list(
                filter(
                    lambda x: x['outputName'] == 'result',
                    result['data']['executePlan']['stepEvents'],
                )
            )[0]
            assert json.loads(
                re.sub('^u\'', '\'', result['valueRepr']).replace('\'', '"')
            ) == json.loads(expected_results[result['step']['solid']['name']].replace('\'', '"'))
