import os
import pytest
import responses

from airflow.operators.bash_operator import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.apache.hive.operators.hive import HiveOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.models import Connection
from dagster import build_op_context, job
from airflow_op_to_dagster_op import operator_to_op
from tempfile import TemporaryDirectory


env_bash_task = BashOperator(
    task_id="env_bash_task",
    bash_command="echo $foo $qux",
    env={"foo": "bar", "qux": "quux"},
)

failure_bash_task = BashOperator(
    task_id="failure_bash_task",
    bash_command="aslkdjalskd",
)


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
    dagster_op = operator_to_op(env_bash_task)
    context = build_op_context()
    dagster_op(context)
    out, _ = capsys.readouterr()
    assert "bar quux" in out


def test_failure_bash_task():
    dagster_op = operator_to_op(failure_bash_task)

    @job
    def my_job():
        dagster_op()

    # TODO: Maybe handle exception?
    with pytest.raises(Exception):
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


def test_docker_task(capsys):
    docker_task = operator_to_op(
        DockerOperator(task_id="docker_task", image='ubuntu', command="/bin/echo 'Hello world'")
    )

    @job
    def my_job():
        docker_task()

    my_job.execute_in_process()

    _, err = capsys.readouterr()

    assert "Hello world" in err


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


def test_hive_operator(capsys):
    # TODO: Hive CLI needs to be installed
    with TemporaryDirectory() as tmpdir:
        connections = [
            Connection(
                conn_id=f'hive_conn',
                host=f"https://mycoolwebsite.com",
            )
        ]

        hql_task = operator_to_op(
            HiveOperator(
                task_id="sqlite_task",
                hql="DROP TABLE IF EXISTS normalized_cereals",
                hive_cli_conn_id="hive_conn",
                mapred_job_name="foo",  # TODO: mandatory param
            ),
            connections=connections,
        )

        @job
        def my_job():
            hql_task()

        my_job.execute_in_process()

    out, _ = capsys.readouterr()
    assert "DROP TABLE IF EXISTS normalized_cereals" in out
    print(out)
    assert False
