from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow.scaffold import scaffold_airflow_dag
from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


def test_scaffold_airflow_dag():
    pipeline = define_demo_execution_pipeline()
    env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

    scaffold_airflow_dag(pipeline, env_config)
