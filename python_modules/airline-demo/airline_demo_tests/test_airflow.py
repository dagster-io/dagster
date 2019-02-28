import datetime
import logging
import os

from airflow.models import TaskInstance

from dagster import execute_pipeline
from dagster.utils import load_yaml_from_glob_list, script_relative_path

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import airflow
from .utils import import_module_from_path


def test_uncontainerized_download_dag_execution_with_airflow_config():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/airflow_base.yml'),
            script_relative_path('../environments/local_fast_download.yml'),
        ]
    )

    result = execute_pipeline(define_airline_demo_download_pipeline(), config_object)

    assert result.success


def test_uncontainerized_ingest_dag_execution_with_airflow_config():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/airflow_base.yml'),
            script_relative_path('../environments/local_ingest.yml'),
        ]
    )

    result = execute_pipeline(define_airline_demo_ingest_pipeline(), config_object)

    assert result.success


def test_uncontainerized_warehouse_dag_execution_with_airflow_config():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/airflow_base.yml'),
            script_relative_path('../environments/local_warehouse.yml'),
        ]
    )

    result = execute_pipeline(define_airline_demo_warehouse_pipeline(), config_object)

    assert result.success


@airflow
class TestInMemoryAirflow_0DownloadDagExecution:
    pipeline = define_airline_demo_download_pipeline
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_download.yml')),
    ]

    def test_airflow_run_download_pipeline(self, scaffold_dag):
        _n, _p, _d, static_path, editable_path = scaffold_dag

        execution_date = datetime.datetime.utcnow()

        import_module_from_path('demo_pipeline_static__scaffold', static_path)
        demo_pipeline = import_module_from_path('demo_pipeline', editable_path)

        _dag, tasks = demo_pipeline.make_dag(
            dag_id=demo_pipeline.DAG_ID,
            dag_description=demo_pipeline.DAG_DESCRIPTION,
            dag_kwargs=dict(default_args=demo_pipeline.DEFAULT_ARGS, **demo_pipeline.DAG_KWARGS),
            s3_conn_id=demo_pipeline.S3_CONN_ID,
            modified_docker_operator_kwargs={
                'persist_intermediate_results_to_s3': True,
                's3_bucket_name': 'dagster-lambda-execution',
            },
            host_tmp_dir=demo_pipeline.HOST_TMP_DIR,
        )

        # These are in topo order already
        for task in tasks:
            ti = TaskInstance(task=task, execution_date=execution_date)
            context = ti.get_template_context()
            task._log = logging  # pylint: disable=protected-access
            task.execute(context)


@airflow
class TestInMemoryAirflow_1IngestExecution:
    pipeline = define_airline_demo_ingest_pipeline
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_ingest.yml')),
    ]

    def test_airflow_run_ingest_pipeline(self, scaffold_dag):
        _n, _p, _d, static_path, editable_path = scaffold_dag

        execution_date = datetime.datetime.utcnow()

        import_module_from_path('demo_pipeline_static__scaffold', static_path)
        demo_pipeline = import_module_from_path('demo_pipeline', editable_path)

        _dag, tasks = demo_pipeline.make_dag(
            dag_id=demo_pipeline.DAG_ID,
            dag_description=demo_pipeline.DAG_DESCRIPTION,
            dag_kwargs=dict(default_args=demo_pipeline.DEFAULT_ARGS, **demo_pipeline.DAG_KWARGS),
            s3_conn_id=demo_pipeline.S3_CONN_ID,
            modified_docker_operator_kwargs={
                'persist_intermediate_results_to_s3': True,
                's3_bucket_name': 'dagster-lambda-execution',
            },
            host_tmp_dir=demo_pipeline.HOST_TMP_DIR,
        )

        # These are in topo order already
        for task in tasks:
            ti = TaskInstance(task=task, execution_date=execution_date)
            context = ti.get_template_context()
            task._log = logging  # pylint: disable=protected-access
            task.execute(context)
