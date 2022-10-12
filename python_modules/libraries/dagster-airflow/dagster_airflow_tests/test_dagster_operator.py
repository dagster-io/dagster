import unittest
from datetime import datetime
from unittest import mock

import pytest
from airflow import DAG
from airflow import __version__ as airflow_version
from airflow.models import Connection, TaskInstance
from dagster_airflow import DagsterCloudOperator
from dagster_airflow_tests.marks import requires_airflow_db


@requires_airflow_db
class TestDagsterOperator(unittest.TestCase):
    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.launch_run", return_value="run_id")
    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.wait_for_run")
    def test_operator(self, launch_run, wait_for_run):
        dag = DAG(dag_id="anydag", start_date=datetime.now())
        run_config = {"foo": "bar"}
        task = DagsterCloudOperator(
            dag=dag,
            task_id="anytask",
            job_name="anyjob",
            run_config=run_config,
            user_token="token",
            organization_id="test-org",
        )
        ti = TaskInstance(task=task, execution_date=datetime.now())
        ctx = ti.get_template_context()
        task.execute(ctx)
        launch_run.assert_called_once()
        wait_for_run.assert_called_once()

    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.launch_run")
    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.wait_for_run")
    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.get_connection")
    @pytest.mark.skipif(airflow_version < "2.0.0", reason="dagster connection requires airflow 2")
    def test_operator_with_connection(self, launch_run, wait_for_run, mock_get_conn):
        mock_connection = Connection(
            conn_type="dagster",
            host="prod",
            password="test-token",
            description="test-org",
        )
        mock_get_conn.return_value = mock_connection

        dag = DAG(dag_id="anydag", start_date=datetime.now())
        run_config = {"foo": "bar"}
        task = DagsterCloudOperator(
            dag=dag, task_id="anytask", job_name="anyjob", run_config=run_config
        )
        ti = TaskInstance(task=task, execution_date=datetime.now())
        ctx = ti.get_template_context()
        task.execute(ctx)
        launch_run.assert_called_once()
        wait_for_run.assert_called_once()
