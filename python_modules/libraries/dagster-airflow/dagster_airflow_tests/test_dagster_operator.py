import unittest
from datetime import datetime, timedelta
from unittest import mock

import pendulum
import pytest
from airflow import (
    DAG,
    __version__ as airflow_version,
)
from airflow.models import Connection, TaskInstance
from dagster_airflow import DagsterCloudOperator

from dagster_airflow_tests.marks import requires_local_db

if airflow_version >= "2.0.0":
    from airflow.utils.state import DagRunState, TaskInstanceState
    from airflow.utils.types import DagRunType


DATA_INTERVAL_START = pendulum.datetime(2021, 9, 13)
DATA_INTERVAL_END = DATA_INTERVAL_START + timedelta(days=1)
if airflow_version >= "2.0.0":
    MOCK_DAGSTER_CONNECTION = Connection(
        conn_type="dagster",
        host="prod",
        password="test-token",
        description="test-org",
    )
else:
    MOCK_DAGSTER_CONNECTION = Connection(
        conn_type="dagster",
        host="prod",
        password="test-token",
    )


@requires_local_db
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
            dagster_conn_id=None,
        )
        if airflow_version >= "2.0.0":
            dagrun = dag.create_dagrun(
                state=DagRunState.RUNNING,
                execution_date=datetime.now(),
                data_interval=(DATA_INTERVAL_START, DATA_INTERVAL_END),
                start_date=DATA_INTERVAL_END,
                run_type=DagRunType.MANUAL,
            )
            ti = dagrun.get_task_instance(task_id="anytask")
            ti.task = dag.get_task(task_id="anytask")
            ti.run(ignore_ti_state=True)
            assert ti.state == TaskInstanceState.SUCCESS
        else:
            ti = TaskInstance(task=task, execution_date=datetime.now())
            ctx = ti.get_template_context()
            task.execute(ctx)
        launch_run.assert_called_once()
        wait_for_run.assert_called_once()

    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.launch_run", return_value="run_id")
    @mock.patch("dagster_airflow.hooks.dagster_hook.DagsterHook.wait_for_run")
    @mock.patch(
        "dagster_airflow.hooks.dagster_hook.DagsterHook.get_connection",
        return_value=MOCK_DAGSTER_CONNECTION,
    )
    @pytest.mark.skipif(airflow_version < "2.0.0", reason="dagster connection requires airflow 2")
    def test_operator_with_connection(self, launch_run, wait_for_run, _mock_get_conn):
        dag = DAG(dag_id="anydag", start_date=datetime.now())
        run_config = {"foo": "bar"}
        DagsterCloudOperator(dag=dag, task_id="anytask", job_name="anyjob", run_config=run_config)
        dagrun = dag.create_dagrun(
            state=DagRunState.RUNNING,
            execution_date=datetime.now(),
            data_interval=(DATA_INTERVAL_START, DATA_INTERVAL_END),
            start_date=DATA_INTERVAL_END,
            run_type=DagRunType.MANUAL,
        )
        ti = dagrun.get_task_instance(task_id="anytask")
        ti.task = dag.get_task(task_id="anytask")
        ti.run(ignore_ti_state=True)
        assert ti.state == TaskInstanceState.SUCCESS
        launch_run.assert_called_once()
        wait_for_run.assert_called_once()
