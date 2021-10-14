import os

from airflow.operators.bash_operator import BashOperator
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
        print(tmpdir)
        simple_bash_task = BashOperator(
            task_id="bash_task", bash_command="touch my_file.txt", cwd=tmpdir
        )

        dagster_op = operator_to_op(simple_bash_task)

        @job
        def my_job():
            dagster_op()

        run_result = my_job.execute_in_process()

        print(os.listdir(tmpdir))
        assert "my_file.txt" in os.listdir(tmpdir)

    # assert run_result.output_for_node("converted_op") == "hello world"
    # for e in run_result.events_for_node("converted_op"):
    #     print(e)
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


test_simple_bash_task()
