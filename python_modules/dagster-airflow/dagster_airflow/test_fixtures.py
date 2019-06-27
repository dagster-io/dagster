import datetime
import uuid

from collections import namedtuple

import pytest

from airflow import DAG
from airflow.models import TaskInstance
from airflow.operators.python_operator import PythonOperator

from dagster.utils import load_yaml_from_glob_list

from .operators import DagsterDockerOperator
from .factory import make_airflow_dag_for_handle, make_airflow_dag_containerized_for_handle


@pytest.fixture(scope='class')
def dagster_airflow_python_operator_pipeline(request):
    '''This is a test fixture for running Dagster pipelines as Airflow DAGs.

    Usage:
        # alternatively, import this fixture into your conftest.py
        from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline

        class TestMyPipeline(object):
            handle = ExecutionTargetHandle.for_pipeline_fn(define_pipeline)
            config = {'solids': {'my_solid': 'foo'}}
            # alternatively, pass a list of globs to be assembled into a config yaml
            # config_yaml = ['environments/test_*.yaml']
            run_id = 'test_run_3'
            execution_date = datetime.datetime(2019, 1, 1)

            def test_pipeline_results(dagster_airflow_python_operator_pipeline):
                # This is a list of the parsed JSON returned by calling executePlan for each
                # solid in the pipeline
                results = dagster_airflow_python_operator_pipeline
                assert len(results) = 3
    '''
    handle = getattr(request.cls, 'handle')
    pipeline_name = getattr(request.cls, 'pipeline_name')
    environment_dict = getattr(request.cls, 'environment_dict', None)
    environment_yaml = getattr(request.cls, 'environment_yaml', None)
    op_kwargs = getattr(request.cls, 'op_kwargs', {})
    mode = getattr(request.cls, 'mode', None)

    if environment_dict is None and environment_yaml is not None:
        environment_dict = load_yaml_from_glob_list(environment_yaml)
    run_id = getattr(request.cls, 'run_id', str(uuid.uuid4()))
    execution_date = getattr(request.cls, 'execution_date', datetime.datetime.utcnow())

    dag, tasks = make_airflow_dag_for_handle(
        handle, pipeline_name, environment_dict, mode=mode, op_kwargs=op_kwargs
    )

    assert isinstance(dag, DAG)

    for task in tasks:
        assert isinstance(task, PythonOperator)

    results = []
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        context['dag_run'] = namedtuple('_', 'run_id')(run_id=run_id)

        res = task.execute(context)
        results.append(res)

    yield results


@pytest.fixture(scope='class')
def dagster_airflow_docker_operator_pipeline(request):
    '''This is a test fixture for running Dagster pipelines as containerized Airflow DAGs.

    Usage:
        # alternatively, import this fixture into your conftest.py
        from dagster_airflow.test_fixtures import dagster_airflow_docker_operator_pipeline

        class TestMyPipeline(object):
            pipeline = define_my_pipeline()
            config = {'solids': {'my_solid': 'foo'}}
            # alternatively, pass a list of globs to be assembled into a config yaml
            # config_yaml = ['environments/test_*.yaml']
            run_id = 'test_run_3'
            execution_date = datetime.datetime(2019, 1, 1)
            image = 'my_pipeline_image'

            def test_pipeline_results(dagster_airflow_docker_operator_pipeline):
                # This is a list of the parsed JSON returned by calling executePlan for each
                # solid in the pipeline
                results = dagster_airflow_docker_operator_pipeline
                assert len(results) = 3
    '''

    handle = getattr(request.cls, 'handle')
    pipeline_name = getattr(request.cls, 'pipeline_name')
    image = getattr(request.cls, 'image')
    environment_dict = getattr(request.cls, 'environment_dict', None)
    environment_yaml = getattr(request.cls, 'environment_yaml', [])
    op_kwargs = getattr(request.cls, 'op_kwargs', {})

    if environment_dict is None and environment_yaml is not None:
        environment_dict = load_yaml_from_glob_list(environment_yaml)
    run_id = getattr(request.cls, 'run_id', str(uuid.uuid4()))
    execution_date = getattr(request.cls, 'execution_date', datetime.datetime.utcnow())

    dag, tasks = make_airflow_dag_containerized_for_handle(
        handle, pipeline_name, image, environment_dict, op_kwargs=op_kwargs
    )

    assert isinstance(dag, DAG)

    for task in tasks:
        assert isinstance(task, DagsterDockerOperator)

    results = []
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        context['dag_run'] = namedtuple('_', 'run_id')(run_id=run_id)

        res = task.execute(context)
        results.append(res)

    yield results
