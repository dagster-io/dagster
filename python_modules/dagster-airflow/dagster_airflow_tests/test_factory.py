from __future__ import unicode_literals

import datetime
import json
import uuid

from collections import namedtuple

from airflow import DAG
from airflow.models import TaskInstance
from airflow.operators.python_operator import PythonOperator

from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow.factory import make_airflow_dag

from .test_project.dagster_airflow_demo import define_demo_execution_pipeline

PIPELINE = define_demo_execution_pipeline()

ENV_CONFIG = load_yaml_from_path(script_relative_path('test_project/env.yml'))


def test_make_dag():
    dag, tasks = make_airflow_dag(PIPELINE, ENV_CONFIG)

    assert isinstance(dag, DAG)
    for task in tasks:
        assert isinstance(task, PythonOperator)


def test_execute_dag():
    _dag, tasks = make_airflow_dag(PIPELINE, ENV_CONFIG)
    run_id = str(uuid.uuid4())
    execution_date = datetime.datetime.utcnow()

    expected_results = {
        'multiply_the_word': '\'barbar\'',
        'count_letters': '{\'b\': 2, \'a\': 2, \'r\': 2}',
    }
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        context['dag_run'] = namedtuple('_', 'run_id')(run_id=run_id)

        res = task.execute(context)
        json_res = json.loads(res)
        assert 'data' in json_res
        assert 'executePlan' in json_res['data']
        assert '__typename' in json_res['data']['executePlan']
        assert json_res['data']['executePlan']['__typename'] == 'ExecutePlanSuccess'
        result = list(
            filter(
                lambda x: x['outputName'] == 'result', json_res['data']['executePlan']['stepEvents']
            )
        )[0]
        assert json.loads(result['valueRepr'].replace('\'', '"')) == json.loads(
            expected_results[task.task_id].replace('\'', '"')
        )
