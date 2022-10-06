from datetime import datetime

from airflow import DAG
from dagster_airflow import DagsterCloudOperator

with DAG(
    dag_id='dagster_cloud',
    start_date=datetime(2022, 5, 28),
    schedule_interval='*/5 * * * *',
    catchup=False,
) as dag:
    DagsterCloudOperator(
        task_id='new_dagster_assets',
        repostitory_location_name="example_location",
        repository_name="my_dagster_project",
        job_name="all_assets_job",
    )
