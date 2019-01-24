# The strings 'airflow' and 'DAG' must both appear in this file in order for it to be parsed by
# airflow as a DAG definition.

import errno
import os

from datetime import datetime, timedelta

# from airflow import DAG
from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow.scaffold import scaffold_airflow_dag

from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


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

pipeline = define_demo_execution_pipeline()
env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

dag = scaffold_airflow_dag(pipeline, env_config)
