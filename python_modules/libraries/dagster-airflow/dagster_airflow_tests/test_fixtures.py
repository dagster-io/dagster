import logging
import sys
import tempfile
from contextlib import contextmanager

import pytest
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.models import TaskInstance
from airflow.settings import LOG_FORMAT
from airflow.utils import timezone
from dagster import file_relative_path
from dagster.core.test_utils import instance_for_test_tempdir
from dagster.core.utils import make_new_run_id
from dagster.utils import load_yaml_from_glob_list, merge_dicts
from dagster.utils.test.postgres_instance import TestPostgresInstance


@contextmanager
def postgres_instance(overrides=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        with TestPostgresInstance.docker_service_up_or_skip(
            file_relative_path(__file__, "docker-compose.yml"),
            "test-postgres-db-airflow",
        ) as pg_conn_string:
            TestPostgresInstance.clean_run_storage(pg_conn_string)
            TestPostgresInstance.clean_event_log_storage(pg_conn_string)
            TestPostgresInstance.clean_schedule_storage(pg_conn_string)
            with instance_for_test_tempdir(
                temp_dir,
                overrides=merge_dicts(
                    {
                        "run_storage": {
                            "module": "dagster_postgres.run_storage.run_storage",
                            "class": "PostgresRunStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "event_log_storage": {
                            "module": "dagster_postgres.event_log.event_log",
                            "class": "PostgresEventLogStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                        "schedule_storage": {
                            "module": "dagster_postgres.schedule_storage.schedule_storage",
                            "class": "PostgresScheduleStorage",
                            "config": {"postgres_url": pg_conn_string},
                        },
                    },
                    overrides if overrides else {},
                ),
            ) as instance:
                yield instance


def execute_tasks_in_dag(dag, tasks, run_id, execution_date):
    assert isinstance(dag, DAG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root = logging.getLogger("airflow.task.operators")
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)

    dag_run = dag.create_dagrun(run_id=run_id, state="success", execution_date=execution_date)

    results = {}
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        context["dag_run"] = dag_run

        try:
            results[ti] = task.execute(context)
        except AirflowSkipException as exc:
            results[ti] = exc

    return results


@pytest.fixture(scope="function")
def dagster_airflow_python_operator_pipeline():
    """This is a test fixture for running Dagster pipelines as Airflow DAGs.

    Usage:
        from dagster_airflow_tests.test_fixtures import dagster_airflow_python_operator_pipeline

        def test_airflow(dagster_airflow_python_operator_pipeline):
            results = dagster_airflow_python_operator_pipeline(
                pipeline_name='test_pipeline',
                recon_repo=reconstructable(define_pipeline),
                environment_yaml=['environments/test_*.yaml']
            )
            assert len(results) == 3
    """
    from dagster_airflow.factory import make_airflow_dag_for_recon_repo
    from dagster_airflow.vendor.python_operator import PythonOperator

    def _pipeline_fn(
        recon_repo,
        pipeline_name,
        run_config=None,
        environment_yaml=None,
        op_kwargs=None,
        mode=None,
        execution_date=timezone.utcnow(),
    ):
        if run_config is None and environment_yaml is not None:
            run_config = load_yaml_from_glob_list(environment_yaml)

        dag, tasks = make_airflow_dag_for_recon_repo(
            recon_repo, pipeline_name, run_config, mode=mode, op_kwargs=op_kwargs
        )
        assert isinstance(dag, DAG)

        for task in tasks:
            assert isinstance(task, PythonOperator)

        return execute_tasks_in_dag(
            dag, tasks, run_id=make_new_run_id(), execution_date=execution_date
        )

    return _pipeline_fn


@pytest.fixture(scope="function")
def dagster_airflow_custom_operator_pipeline():
    """This is a test fixture for running Dagster pipelines with custom operators as Airflow DAGs.

    Usage:
        from dagster_airflow_tests.test_fixtures import dagster_airflow_custom_operator_pipeline

        def test_airflow(dagster_airflow_python_operator_pipeline):
            results = dagster_airflow_custom_operator_pipeline(
                pipeline_name='test_pipeline',
                recon_repo=reconstructable(define_pipeline),
                operator=MyCustomOperator,
                environment_yaml=['environments/test_*.yaml']
            )
            assert len(results) == 3
    """
    from dagster_airflow.factory import make_airflow_dag_for_operator
    from dagster_airflow.vendor.python_operator import PythonOperator

    def _pipeline_fn(
        recon_repo,
        pipeline_name,
        operator,
        run_config=None,
        environment_yaml=None,
        op_kwargs=None,
        mode=None,
        execution_date=timezone.utcnow(),
    ):
        if run_config is None and environment_yaml is not None:
            run_config = load_yaml_from_glob_list(environment_yaml)

        dag, tasks = make_airflow_dag_for_operator(
            recon_repo, pipeline_name, operator, run_config, mode=mode, op_kwargs=op_kwargs
        )
        assert isinstance(dag, DAG)

        for task in tasks:
            assert isinstance(task, PythonOperator)

        return execute_tasks_in_dag(
            dag, tasks, run_id=make_new_run_id(), execution_date=execution_date
        )

    return _pipeline_fn


@pytest.fixture(scope="function")
def dagster_airflow_docker_operator_pipeline():
    """This is a test fixture for running Dagster pipelines as containerized Airflow DAGs.

    Usage:
        from dagster_airflow_tests.test_fixtures import dagster_airflow_docker_operator_pipeline

        def test_airflow(dagster_airflow_docker_operator_pipeline):
            results = dagster_airflow_docker_operator_pipeline(
                pipeline_name='test_pipeline',
                recon_repo=reconstructable(define_pipeline),
                environment_yaml=['environments/test_*.yaml'],
                image='myimage:latest'
            )
            assert len(results) == 3
    """
    from dagster_airflow.factory import make_airflow_dag_containerized_for_recon_repo
    from dagster_airflow.operators.docker_operator import DagsterDockerOperator

    def _pipeline_fn(
        recon_repo,
        pipeline_name,
        image,
        run_config=None,
        environment_yaml=None,
        op_kwargs=None,
        mode=None,
        execution_date=timezone.utcnow(),
    ):
        if run_config is None and environment_yaml is not None:
            run_config = load_yaml_from_glob_list(environment_yaml)

        op_kwargs = op_kwargs or {}
        op_kwargs["network_mode"] = "container:test-postgres-db-airflow"

        with postgres_instance() as instance:

            dag, tasks = make_airflow_dag_containerized_for_recon_repo(
                recon_repo=recon_repo,
                pipeline_name=pipeline_name,
                image=image,
                mode=mode,
                run_config=run_config,
                op_kwargs=op_kwargs,
                instance=instance,
            )
            assert isinstance(dag, DAG)

            for task in tasks:
                assert isinstance(task, DagsterDockerOperator)

            return execute_tasks_in_dag(
                dag, tasks, run_id=make_new_run_id(), execution_date=execution_date
            )

    return _pipeline_fn
