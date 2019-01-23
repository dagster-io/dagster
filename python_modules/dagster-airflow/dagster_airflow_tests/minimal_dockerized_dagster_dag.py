import errno
import os

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.dagster_plugin import DagsterOperator


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


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
    docker_url=os.getenv('DOCKER_HOST'),
    command='pipeline execute demo_pipeline -e env.yml',
    image='dagster-airflow-demo:latest',
    network_mode='bridge',
    task_id='minimal_dockerized_dagster_airflow_node',
    dag=dag,
    host_tmp_dir='/tmp/airflow',
    tmp_dir='/tmp/airflow',
)
