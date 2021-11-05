import os
import pytest
import responses
import json

from airflow.operators.bash_operator import BashOperator

from airflow.operators.python_operator import PythonOperator
from airflow.operators.sqlite_operator import SqliteOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import Connection
from dagster import build_op_context, job
from dagster_airflow import operator_to_op
from tempfile import TemporaryDirectory

from dagster_gcp_tests.gcs_tests.conftest import gcs_bucket  # pylint: disable=unused-import
from dagster.core.test_utils import instance_for_test

from dagster_tests.core_tests.test_python_logging import get_log_records


def test_simple_bash_task():
    with TemporaryDirectory() as tmpdir:
        simple_bash_task = BashOperator(
            task_id="bash_task", bash_command=f"cd {tmpdir}; touch my_file.txt"
        )

        dagster_op = operator_to_op(simple_bash_task)

        @job
        def my_job():
            dagster_op()

        run_result = my_job.execute_in_process()

        assert "my_file.txt" in os.listdir(tmpdir)


def test_env_bash_task(capsys):
    with TemporaryDirectory() as tmpdir:
        env_bash_task = BashOperator(
            task_id="env_bash_task",
            bash_command=f"cd {tmpdir}; touch $foo",
            env={"foo": "bar.txt"},
        )

        dagster_op = operator_to_op(env_bash_task)

        @job
        def my_job():
            dagster_op()

        run_result = my_job.execute_in_process()

        assert "bar.txt" in os.listdir(tmpdir)


def test_failure_bash_task():
    failure_bash_task = BashOperator(
        task_id="failure_bash_task",
        bash_command="aslkdjalskd",
    )
    dagster_op = operator_to_op(failure_bash_task)

    @job
    def my_job():
        dagster_op()

    with pytest.raises(Exception, match="Bash command failed"):
        my_job.execute_in_process()


def test_http_task():
    http_task = SimpleHttpOperator(task_id="http_task", endpoint="foo")

    connections = [Connection(conn_id=f'http_default', host="https://mycoolwebsite.com")]

    dagster_op = operator_to_op(http_task, connections=connections)

    @job
    def my_job():
        dagster_op()

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.POST, "https://mycoolwebsite.com/foo", body="foo")
        result = my_job.execute_in_process()
        assert result.success
        assert len(rsps.calls) == 1
        response = rsps.calls[0].response
        assert response.content == b"foo"


def test_capture_op_logs():

    env_bash_task = BashOperator(
        task_id="capture_logs_task",
        bash_command=f"echo $foo",
        env={"foo": "quux"},
    )

    dagster_op = operator_to_op(env_bash_task)

    @job
    def my_job():
        dagster_op()

    with instance_for_test() as instance:
        result = my_job.execute_in_process(instance=instance)

        event_records = [
            lr
            for lr in instance.event_log_storage.get_logs_for_run(result.run_id)
            if lr.user_message == "quux"
        ]

        assert len(event_records) == 1


def test_capture_hook_logs():
    http_task = SimpleHttpOperator(task_id="capture_logs_http_task", endpoint="foo")

    connections = [Connection(conn_id=f'http_default', host="https://mycoolwebsite.com")]

    dagster_op = operator_to_op(http_task, connections=connections)

    @job
    def my_job():
        dagster_op()

    with instance_for_test() as instance:
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, "https://mycoolwebsite.com/foo", body="foo")
            result = my_job.execute_in_process(instance=instance)

            event_records = [
                lr
                for lr in instance.event_log_storage.get_logs_for_run(result.run_id)
                if "https://mycoolwebsite.com/foo" in lr.user_message
            ]

            assert len(event_records) == 1


def test_return_output_xcom():
    def my_python_func():
        return "foo"

    simple_python_task = PythonOperator(
        task_id="python_task", python_callable=my_python_func, xcom_push=True
    )

    dagster_op = operator_to_op(simple_python_task, return_output=True)

    @job
    def my_job():
        dagster_op()

    result = my_job.execute_in_process()
    assert result.output_for_node("python_task") == "foo"


def chain_converted_op_output():
    def my_python_func():
        return 100

    simple_python_task = PythonOperator(
        task_id="python_task", python_callable=my_python_func, xcom_push=True
    )
    dagster_op = operator_to_op(simple_python_task, return_output=True)

    @op
    def mult_by_two(num):
        return num * 2

    @job
    def my_job():
        mult_by_two(dagster_op())

    result = my_job.execute_in_process()
    assert result.output_for_node("mult_by_two") == 200


def test_sqlite_operator(capsys):
    with TemporaryDirectory() as tmpdir:
        connections = [
            Connection(
                conn_id=f'sql_alchemy_conn',
                host=f"{tmpdir}/example.db",
                login="",
                password="",
            )
        ]

        sqlite_task = operator_to_op(
            SqliteOperator(
                task_id="sqlite_task",
                sql="DROP TABLE IF EXISTS normalized_cereals",
                sqlite_conn_id="sql_alchemy_conn",
            ),
            connections=connections,
        )

        @job
        def my_job():
            sqlite_task()

        my_job.execute_in_process()

    out, _ = capsys.readouterr()
    assert "DROP TABLE IF EXISTS normalized_cereals" in out
