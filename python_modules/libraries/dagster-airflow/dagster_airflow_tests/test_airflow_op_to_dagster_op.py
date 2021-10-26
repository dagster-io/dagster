import os
import responses

from airflow.operators.bash_operator import BashOperator
from airflow.operators.http_operator import SimpleHttpOperator
from dagster import build_op_context, job
from dagster_airflow import operator_to_op
from tempfile import TemporaryDirectory


env_bash_task = BashOperator(
    task_id="env_bash_task",
    bash_command="echo $one $two",
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


def test_http_task():
    http_task = SimpleHttpOperator(task_id="http_task", endpoint="foo")

    dagster_op = operator_to_op(http_task)

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

    assert False


def test_env_bash_task(capsys):
    dagster_op = operator_to_op(env_bash_task)
    context = build_op_context()
    dagster_op(context)
    out, _ = capsys.readouterr()
    print(out)
    assert "hello world" in out


def test_failure_bash_task(capsys):
    dagster_op = operator_to_op(failure_bash_task, capture_logs=True, return_output=True)

    @job
    def my_job():
        # context = build_op_context()
        dagster_op()

    my_job.execute_in_process()

    out, err = capsys.readouterr()
    print(out)
    print(err)
    assert "hello world" in out
