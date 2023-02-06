import pendulum
import pytest
from airflow import __version__ as airflow_version
from airflow.models.dag import DAG
from dagster_airflow.dagster_schedule_factory import make_dagster_schedule_from_airflow_dag


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
def test_schedule_timezone():
    args = {
        "owner": "airflow",
        "start_date": pendulum.today("Europe/London").add(days=-2),
    }
    dag = DAG(
        dag_id="test_schedules",
        default_args=args,
        schedule="0 0 * * *",
    )

    schedule = make_dagster_schedule_from_airflow_dag(dag=dag)
    assert schedule.cron_schedule == "0 0 * * *"
    assert schedule.execution_timezone == "Europe/London"
