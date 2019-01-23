from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.dagster_plugin import DagsterOperator

from dagster.utils import mkdir_p

mkdir_p('/tmp/airflow')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.utcnow(),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'minimal_dockerized_dagster_airflow_demo',
    default_args=default_args,
    schedule_interval=timedelta(minutes=10),
)

t1 = DagsterOperator(
    api_version='1.21',
    # docker_url='tcp://localhost:2375',  # Set your docker URL
    command='pipeline execute demo_pipeline -e env.yml',
    image='dagster-airflow-demo:latest',
    network_mode='bridge',
    task_id='minimal_dockerized_dagster_airflow_node',
    dag=dag,
    host_tmp_dir='/tmp/airflow',
    tmp_dir='/tmp/airflow',
)
