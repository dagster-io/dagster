import datetime
import os
import subprocess
from unittest import mock

from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator
from airflow.models.dag import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
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


# Airflow DAG ids and Task ids allow a larger valid character set (alphanumeric characters,
# dashes, dots and underscores) than Dagster's naming conventions (alphanumeric characters,
# underscores), so Dagster will strip invalid characters and replace with '_'
def test_normalize_name():
    dag = DAG(
        dag_id="dag-with.dot-dash",
        default_args=default_args,
        schedule_interval=None,
    )
    dummy_operator = DummyOperator(
        task_id="task-with.dot-dash",
        dag=dag,
    )

    pipeline_def = make_dagster_pipeline_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    result = execute_pipeline(pipeline_def)

    assert result.success
    assert result.pipeline_def.name == "airflow_dag_with_dot_dash"
    assert len(result.pipeline_def.solids) == 1
    assert result.pipeline_def.solids[0].name == "airflow_task_with_dot_dash"


# Test names with 250 characters, Airflow's max allowed length
def test_long_name():
    dag_name = "dag-with.dot-dash-lo00ong" * 10
    dag = DAG(
        dag_id=dag_name,
        default_args=default_args,
        schedule_interval=None,
    )
    long_name = "task-with.dot-dash2-loong" * 10  # 250 characters, Airflow's max allowed length
    dummy_operator = DummyOperator(
        task_id=long_name,
        dag=dag,
    )

    pipeline_def = make_dagster_pipeline_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    result = execute_pipeline(pipeline_def)

    assert result.success
    assert (
        result.pipeline_def.name
        == "airflow_dag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ong"
    )

    assert len(result.pipeline_def.solids) == 1
    assert (
        result.pipeline_def.solids[0].name
        == "airflow_task_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loong"
    )


def test_one_task_dag():
    dag = DAG(
        dag_id="dag",
        default_args=default_args,
        schedule_interval=None,
    )
    dummy_operator = DummyOperator(
        task_id="dummy_operator",
        dag=dag,
    )

    pipeline_def = make_dagster_pipeline_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    result = execute_pipeline(pipeline_def)
    assert result.success


def normalize_file_content(s):
    return "\n".join([line for line in s.replace(os.linesep, "\n").split("\n") if line])


def test_template_task_dag():
    dag = DAG(
        dag_id="dag",
        default_args=default_args,
        schedule_interval=None,
    )

    t1 = BashOperator(
        task_id="print_hello",
        bash_command="echo hello dagsir",
        dag=dag,
    )

    t2 = BashOperator(
        task_id="sleep",
        bash_command="sleep 2",
        dag=dag,
    )

    templated_command = """
    {% for i in range(5) %}
        echo '{{ ds }}'
        echo '{{ macros.ds_add(ds, 7)}}'
        echo '{{ params.my_param }}'
    {% endfor %}
    """

    t3 = BashOperator(
        task_id="templated",
        depends_on_past=False,
        bash_command=templated_command,
        params={"my_param": "Parameter I passed in"},
        dag=dag,
    )

    # pylint: disable=pointless-statement
    t1 >> [t2, t3]

    with instance_for_test() as instance:
        manager = instance.compute_log_manager

        execution_date = get_current_datetime_in_utc()
        execution_date_add_one_week = execution_date + datetime.timedelta(days=7)
        execution_date_iso = execution_date.strftime("%Y-%m-%d")
        execution_date_add_one_week_iso = execution_date_add_one_week.strftime("%Y-%m-%d")

        result = execute_pipeline(
            make_dagster_pipeline_from_airflow_dag(
                dag=dag, tags={AIRFLOW_EXECUTION_DATE_STR: execution_date_iso}
            ),
            instance=instance,
        )

        compute_steps = [
            event.step_key
            for event in result.step_event_list
            if event.event_type == DagsterEventType.STEP_START
        ]

        assert compute_steps == [
            "airflow_print_hello",
            "airflow_sleep",
            "airflow_templated",
        ]

        for step_key in compute_steps:
            compute_io_path = manager.get_local_path(result.run_id, step_key, ComputeIOType.STDOUT)
            assert os.path.exists(compute_io_path)
            stdout_file = open(compute_io_path, "r")
            file_contents = normalize_file_content(stdout_file.read())
            stdout_file.close()

            if step_key == "airflow_print_hello":
                assert file_contents.count("INFO - Running command: echo hello dagsir\n") == 1
                assert file_contents.count("INFO - Command exited with return code 0") == 1

            elif step_key == "airflow_sleep":
                assert file_contents.count("INFO - Running command: sleep 2\n") == 1
                assert file_contents.count("INFO - Output:\n") == 1
                assert file_contents.count("INFO - Command exited with return code 0") == 1

            elif step_key == "airflow_templated":
                assert (
                    file_contents.count(
                        "INFO - Running command: \n    \n        "
                        "echo '{execution_date_iso}'\n        "
                        "echo '{execution_date_add_one_week_iso}'\n        "
                        "echo 'Parameter I passed in'\n    \n        "
                        "echo '{execution_date_iso}'\n        "
                        "echo '{execution_date_add_one_week_iso}'\n        "
                        "echo 'Parameter I passed in'\n    \n        "
                        "echo '{execution_date_iso}'\n        "
                        "echo '{execution_date_add_one_week_iso}'\n        "
                        "echo 'Parameter I passed in'\n    \n        "
                        "echo '{execution_date_iso}'\n        "
                        "echo '{execution_date_add_one_week_iso}'\n        "
                        "echo 'Parameter I passed in'\n    \n        "
                        "echo '{execution_date_iso}'\n        "
                        "echo '{execution_date_add_one_week_iso}'\n        "
                        "echo 'Parameter I passed in'\n    \n    \n".format(
                            execution_date_iso=execution_date_iso,
                            execution_date_add_one_week_iso=execution_date_add_one_week_iso,
                        )
                    )
                    == 1
                )
                assert (
                    file_contents.count(
                        "INFO - {execution_date_iso}\n".format(
                            execution_date_iso=execution_date_iso
                        )
                    )
                    == 5
                )
                assert (
                    file_contents.count(
                        "INFO - {execution_date_add_one_week_iso}\n".format(
                            execution_date_add_one_week_iso=execution_date_add_one_week_iso
                        )
                    )
                    == 5
                )
                assert file_contents.count("INFO - Parameter I passed in\n") == 5
                assert file_contents.count("INFO - Command exited with return code 0") == 1


def intercept_spark_submit(*args, **kwargs):
    if args[0] == ["spark-submit", "--master", "", "--name", "airflow-spark", "some_path.py"]:
        m = mock.MagicMock()
        m.stdout.readline.return_value = ""
        m.wait.return_value = 0
        return m
    else:
        return subprocess.Popen(*args, **kwargs)


@mock.patch("subprocess.Popen", side_effect=intercept_spark_submit)
def test_spark_dag(mock_subproc_popen):
    # Hack to get around having a Connection
    os.environ["AIRFLOW_CONN_SPARK"] = "something"

    dag = DAG(
        dag_id="spark_dag",
        default_args=default_args,
        schedule_interval=None,
    )
    # pylint: disable=unused-variable
    clean_data = SparkSubmitOperator(
        task_id="run_spark",
        application="some_path.py",
        conn_id="SPARK",
        dag=dag,
    )

    pipeline = make_dagster_pipeline_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    execute_pipeline(pipeline)  # , instance=instance,)

    assert mock_subproc_popen.call_args_list[0][0] == (
        ["spark-submit", "--master", "", "--name", "airflow-spark", "some_path.py"],
    )
