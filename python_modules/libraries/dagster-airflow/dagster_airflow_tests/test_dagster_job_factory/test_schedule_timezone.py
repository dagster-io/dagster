import pendulum
from airflow.models.dag import DAG
from dagster_airflow.dagster_pipeline_factory import \
    make_dagster_schedule_from_airflow_dag

from dagster import job


def test_schedule_timezone():
    args = {
        'owner': 'airflow',
        'start_date': pendulum.today('Europe/London').add(days=-2),
    }
    dag = DAG(
        dag_id='test_schedules',
        default_args=args,
        schedule='0 0 * * *',

    )
    @job
    def job_def():
        return

    schedule = make_dagster_schedule_from_airflow_dag(
        dag=dag,
        job_def=job_def
    )
    assert schedule.cron_schedule == '0 0 * * *'
    assert schedule.execution_timezone == 'Europe/London'