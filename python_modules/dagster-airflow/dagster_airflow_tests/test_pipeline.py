import pytest

from dagster import execute_pipeline
from dagster.utils import load_yaml_from_glob_list, script_relative_path

from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


@pytest.mark.skip
def test_execute_demo_pipeline():
    pipeline = define_demo_execution_pipeline()
    config = load_yaml_from_glob_list([script_relative_path('test_project/env.yml')])

    execute_pipeline(pipeline, config)
