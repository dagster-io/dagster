import datetime
import os

import pytest
from airflow import __version__ as airflow_version
from airflow.models.dag import DAG
from airflow.operators.bash_operator import BashOperator  # type: ignore
from airflow.utils.dates import days_ago
from dagster import DagsterEventType
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._core.test_utils import instance_for_test
from dagster._time import get_current_datetime
from dagster_airflow import make_dagster_job_from_airflow_dag

default_args = {
    "owner": "dagster",
    "start_date": days_ago(10),
}

EXECUTION_DATE = get_current_datetime()
EXECUTION_DATE_MINUS_WEEK = EXECUTION_DATE - datetime.timedelta(days=7)

EXECUTION_DATE_FMT = EXECUTION_DATE.isoformat()
EXECUTION_DATE_MINUS_WEEK_FMT = EXECUTION_DATE_MINUS_WEEK.isoformat()


def normalize_file_content(s):
    return "\n".join([line for line in s.replace(os.linesep, "\n").split("\n") if line])


def check_captured_logs(manager, result, execution_date_fmt):
    assert result.success
    assert isinstance(manager, LocalComputeLogManager)

    capture_events = [
        event for event in result.all_events if event.event_type == DagsterEventType.LOGS_CAPTURED
    ]
    assert len(capture_events) == 1
    event = capture_events[0]
    assert event.logs_captured_data.step_keys == ["test_tags_dag__templated"]
    log_key = [result.run_id, "compute_logs", event.logs_captured_data.file_key]
    compute_io_path = manager.get_captured_local_path(
        log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
    )
    assert os.path.exists(compute_io_path)
    stdout_file = open(compute_io_path, encoding="utf8")
    file_contents = normalize_file_content(stdout_file.read())
    stdout_file.close()

    # assert 1 == 0
    assert file_contents.count("Running command:") == 1
    assert file_contents.count(f"command for dt {execution_date_fmt}") == 2
    assert file_contents.count("Command exited with return code 0") == 1


def get_dag():
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="test_tags_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="test_tags_dag",
            default_args=default_args,
            schedule_interval=None,
        )

    templated_command = """
    echo 'command for dt {{ ds }}'
    """

    _t1 = BashOperator(
        task_id="templated",
        depends_on_past=False,
        bash_command=templated_command,
        dag=dag,
    )

    return dag


@pytest.mark.requires_no_db
def test_job_tags():
    dag = get_dag()

    with instance_for_test() as instance:
        manager = instance.compute_log_manager

        # When mode is default and tags are set, run with tags
        job_def = make_dagster_job_from_airflow_dag(
            dag=dag,
            tags={AIRFLOW_EXECUTION_DATE_STR: EXECUTION_DATE_MINUS_WEEK_FMT},
        )
        result = job_def.execute_in_process(instance=instance)

        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"

        check_captured_logs(manager, result, EXECUTION_DATE_MINUS_WEEK.strftime("%Y-%m-%d"))


@pytest.mark.requires_no_db
def test_job_auto_tag():
    dag = get_dag()

    with instance_for_test() as instance:
        manager = instance.compute_log_manager
        assert isinstance(manager, LocalComputeLogManager)

        pre_execute_time = get_current_datetime()

        # When tags are not set, run with current time
        job_def = make_dagster_job_from_airflow_dag(
            dag=dag,
        )
        result = job_def.execute_in_process(instance=instance)
        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"

        capture_events = [
            event
            for event in result.all_events
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        event = capture_events[0]
        assert event.logs_captured_data.step_keys == ["test_tags_dag__templated"]
        post_execute_time = get_current_datetime()

        log_key = [result.run_id, "compute_logs", event.logs_captured_data.file_key]
        compute_io_path = manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
        )
        assert os.path.exists(compute_io_path)
        stdout_file = open(compute_io_path, encoding="utf8")
        file_contents = normalize_file_content(stdout_file.read())

        stdout_file.close()

        search_str = "command for dt "
        date_start = file_contents.find(search_str) + len(search_str)
        date_end = date_start + 10  # number of characters in YYYY-MM-DD
        date = file_contents[date_start:date_end]

        check_captured_logs(manager, result, date)

        pre_execute_time_fmt = pre_execute_time.strftime("%Y-%m-%d")
        post_execute_time_fmt = post_execute_time.strftime("%Y-%m-%d")

        assert date in [pre_execute_time_fmt, post_execute_time_fmt]
