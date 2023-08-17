import datetime
import os
from unittest import mock

# We ignore type errors in several places because we are importing in such a way as to be
# compatible with both versions 1.x and 2.x of airflow. This means importing from places that are
# not the blessed API of the latest version, which raises pyright "not exported" errors.
from airflow import __version__ as airflow_version

if airflow_version >= "2.0.0":
    from airflow.providers.apache.spark.operators.spark_submit import (
        SparkSubmitOperator,
    )
else:
    from airflow.contrib.operators.spark_submit_operator import (  # type: ignore (airflow 1 compat)
        SparkSubmitOperator,
    )

from airflow.models.dag import DAG
from airflow.operators.bash_operator import BashOperator  # type: ignore (airflow 1 compat)
from airflow.operators.dummy_operator import DummyOperator  # type: ignore (airflow 1 compat)
from airflow.utils.dates import days_ago
from dagster import DagsterEventType
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR
from dagster._core.test_utils import instance_for_test
from dagster._seven import get_current_datetime_in_utc
from dagster_airflow import make_dagster_job_from_airflow_dag

from dagster_airflow_tests.marks import requires_no_db

default_args = {
    "owner": "dagster",
    "start_date": days_ago(1),
}


# Airflow DAG ids and Task ids allow a larger valid character set (alphanumeric characters,
# dashes, dots and underscores) than Dagster's naming conventions (alphanumeric characters,
# underscores), so Dagster will strip invalid characters and replace with '_'
@requires_no_db
def test_normalize_name():
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="dag-with.dot-dash",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="dag-with.dot-dash",
            default_args=default_args,
            schedule_interval=None,
        )
    _dummy_operator = DummyOperator(
        task_id="task-with.dot-dash",
        dag=dag,
    )

    job_def = make_dagster_job_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    result = job_def.execute_in_process()

    assert result.success
    assert result.job_def.name == "dag_with_dot_dash"
    assert len(result.job_def.nodes) == 1
    assert result.job_def.nodes[0].name == "dag_with_dot_dash__task_with_dot_dash"


# Test names with 250 characters, Airflow's max allowed length
@requires_no_db
def test_long_name():
    dag_name = "dag-with.dot-dash-lo00ong" * 10
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id=dag_name,
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id=dag_name,
            default_args=default_args,
            schedule_interval=None,
        )
    long_name = "task-with.dot-dash2-loong" * 10  # 250 characters, Airflow's max allowed length
    _dummy_operator = DummyOperator(
        task_id=long_name,
        dag=dag,
    )

    job_def = make_dagster_job_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    result = job_def.execute_in_process()

    assert result.success
    assert (
        result.job_def.name
        == "dag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ong"
    )

    assert len(result.job_def.nodes) == 1
    assert (
        result.job_def.nodes[0].name
        == "dag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ongdag_with_dot_dash_lo00ong__task_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loongtask_with_dot_dash2_loong"
    )


@requires_no_db
def test_one_task_dag():
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="dag",
            default_args=default_args,
            schedule_interval=None,
        )
    _dummy_operator = DummyOperator(
        task_id="dummy_operator",
        dag=dag,
    )

    job_def = make_dagster_job_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    result = job_def.execute_in_process()
    assert result.success


def normalize_file_content(s):
    return "\n".join([line for line in s.replace(os.linesep, "\n").split("\n") if line])


@requires_no_db
def test_template_task_dag(tmpdir):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="dag",
            default_args=default_args,
            schedule_interval=None,
        )

    print_hello_out = tmpdir / "print_hello.out"
    t1 = BashOperator(
        task_id="print_hello",
        bash_command=f"echo hello dagsir > {print_hello_out}",
        dag=dag,
    )

    sleep_out = tmpdir / "sleep"
    t2 = BashOperator(
        task_id="sleep",
        bash_command=f"sleep 2; touch {sleep_out}",
        dag=dag,
    )

    templated_out = tmpdir / "templated.out"
    templated_command = """
    {% for i in range(5) %}
        echo '{{ ds }}' >> {{ params.out_file }}
        echo '{{ macros.ds_add(ds, 7)}}' >> {{ params.out_file }}
    {% endfor %}
    """

    t3 = BashOperator(
        task_id="templated",
        depends_on_past=False,
        bash_command=templated_command,
        params={"out_file": templated_out},
        dag=dag,
    )

    t1 >> [t2, t3]

    with instance_for_test() as instance:
        execution_date = get_current_datetime_in_utc()
        execution_date_add_one_week = execution_date + datetime.timedelta(days=7)
        execution_date_iso = execution_date.isoformat()

        job_def = make_dagster_job_from_airflow_dag(
            dag=dag, tags={AIRFLOW_EXECUTION_DATE_STR: execution_date_iso}
        )

        assert not os.path.exists(print_hello_out)
        assert not os.path.exists(sleep_out)
        assert not os.path.exists(templated_out)

        result = job_def.execute_in_process(instance=instance)

        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"

        capture_events = [
            event
            for event in result._event_list  # noqa: SLF001
            if event.event_type == DagsterEventType.LOGS_CAPTURED
        ]
        assert len(capture_events) == 1
        event = capture_events[0]
        assert event.logs_captured_data.step_keys == [
            "dag__print_hello",
            "dag__sleep",
            "dag__templated",
        ]

        assert os.path.exists(print_hello_out)
        assert "hello dagsir" in print_hello_out.read()

        assert os.path.exists(sleep_out)

        assert os.path.exists(templated_out)
        assert templated_out.read().count(execution_date.strftime("%Y-%m-%d")) == 5
        assert templated_out.read().count(execution_date_add_one_week.strftime("%Y-%m-%d")) == 5


def intercept_spark_submit(*_args, **_kwargs):
    m = mock.MagicMock()
    m.stdout.readline.return_value = ""
    m.wait.return_value = 0
    return m


@requires_no_db
@mock.patch("subprocess.Popen", side_effect=intercept_spark_submit)
def test_spark_dag(mock_subproc_popen):
    # Hack to get around having a Connection
    os.environ["AIRFLOW_CONN_SPARK"] = "something"

    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="spark_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="spark_dag",
            default_args=default_args,
            schedule_interval=None,
        )
    SparkSubmitOperator(
        task_id="run_spark",
        application="some_path.py",
        conn_id="SPARK",
        dag=dag,
    )
    job_def = make_dagster_job_from_airflow_dag(
        dag=dag,
        tags={AIRFLOW_EXECUTION_DATE_STR: get_current_datetime_in_utc().isoformat()},
    )
    job_def.execute_in_process()

    if airflow_version >= "2.0.0":
        assert mock_subproc_popen.call_args_list[0][0] == (
            ["spark-submit", "--master", "", "--name", "arrow-spark", "some_path.py"],
        )
    else:
        assert mock_subproc_popen.call_args_list[0][0] == (
            ["spark-submit", "--master", "", "--name", "airflow-spark", "some_path.py"],
        )
