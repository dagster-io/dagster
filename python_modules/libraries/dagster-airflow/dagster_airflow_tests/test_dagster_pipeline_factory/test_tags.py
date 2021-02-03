import datetime
import os

from airflow.models.dag import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
from dagster import DagsterEventType, execute_pipeline
from dagster.core.instance import AIRFLOW_EXECUTION_DATE_STR
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.test_utils import instance_for_test
from dagster.seven import get_current_datetime_in_utc
from dagster_airflow.dagster_pipeline_factory import make_dagster_pipeline_from_airflow_dag

default_args = {
    "owner": "dagster",
    "start_date": days_ago(1),
}

EXECUTION_DATE = get_current_datetime_in_utc()
EXECUTION_DATE_MINUS_WEEK = EXECUTION_DATE - datetime.timedelta(days=7)

EXECUTION_DATE_FMT = EXECUTION_DATE.strftime("%Y-%m-%d")
EXECUTION_DATE_MINUS_WEEK_FMT = EXECUTION_DATE_MINUS_WEEK.strftime("%Y-%m-%d")


def normalize_file_content(s):
    return "\n".join([line for line in s.replace(os.linesep, "\n").split("\n") if line])


def check_compute_logs(manager, result, execution_date_fmt):
    assert result.success

    compute_steps = [
        event.step_key
        for event in result.step_event_list
        if event.event_type == DagsterEventType.STEP_START
    ]

    assert compute_steps == [
        "airflow_templated",
    ]

    for step_key in compute_steps:
        compute_io_path = manager.get_local_path(result.run_id, step_key, ComputeIOType.STDOUT)
        assert os.path.exists(compute_io_path)
        stdout_file = open(compute_io_path, "r")
        file_contents = normalize_file_content(stdout_file.read())
        stdout_file.close()

        assert (
            file_contents.count(
                "INFO - Running command: \n    echo '{execution_date_fmt}'\n".format(
                    execution_date_fmt=execution_date_fmt
                )
            )
            == 1
        )
        assert (
            file_contents.count(
                "INFO - {execution_date_fmt}\n".format(execution_date_fmt=execution_date_fmt)
            )
            == 1
        )
        assert file_contents.count("INFO - Command exited with return code 0") == 1


def get_dag():
    dag = DAG(
        dag_id="dag",
        default_args=default_args,
        schedule_interval=None,
    )

    templated_command = """
    echo '{{ ds }}'
    """

    # pylint: disable=unused-variable
    t1 = BashOperator(
        task_id="templated",
        depends_on_past=False,
        bash_command=templated_command,
        dag=dag,
    )

    return dag


def test_pipeline_tags():
    dag = get_dag()

    with instance_for_test() as instance:
        manager = instance.compute_log_manager

        # When mode is default and tags are set, run with tags
        result = execute_pipeline(
            pipeline=make_dagster_pipeline_from_airflow_dag(
                dag=dag, tags={AIRFLOW_EXECUTION_DATE_STR: EXECUTION_DATE_MINUS_WEEK_FMT}
            ),
            instance=instance,
        )
        check_compute_logs(manager, result, EXECUTION_DATE_MINUS_WEEK_FMT)


def test_pipeline_auto_tag():
    dag = get_dag()

    with instance_for_test() as instance:
        manager = instance.compute_log_manager

        pre_execute_time = get_current_datetime_in_utc()

        # When tags are not set, run with current time
        result = execute_pipeline(
            pipeline=make_dagster_pipeline_from_airflow_dag(dag=dag),
            instance=instance,
        )

        post_execute_time = get_current_datetime_in_utc()

        compute_io_path = manager.get_local_path(
            result.run_id, "airflow_templated", ComputeIOType.STDOUT
        )
        assert os.path.exists(compute_io_path)
        stdout_file = open(compute_io_path, "r")
        file_contents = normalize_file_content(stdout_file.read())

        stdout_file.close()

        search_str = "INFO - Running command: \n    echo '"
        date_start = file_contents.find(search_str) + len(search_str)
        date_end = date_start + 10  # number of characters in YYYY-MM-DD
        date = file_contents[date_start:date_end]

        check_compute_logs(manager, result, date)

        pre_execute_time_fmt = pre_execute_time.strftime("%Y-%m-%d")
        post_execute_time_fmt = post_execute_time.strftime("%Y-%m-%d")

        assert date in [pre_execute_time_fmt, post_execute_time_fmt]
