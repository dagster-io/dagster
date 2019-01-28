import datetime
import os
import shutil

from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow.scaffold import scaffold_airflow_dag
from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


DAG_DEFINITION_FILENAME = 'minimal_dockerized_dagster_dag.py'


def test_scaffold_airflow_dag(airflow_test, dags_path):
    pipeline = define_demo_execution_pipeline()
    env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

    scaffold_airflow_dag(
        pipeline,
        env_config,
        image='dagster-airflow-demo',
        output_path=script_relative_path(DAG_DEFINITION_FILENAME),
    )

    shutil.copyfile(
        script_relative_path(DAG_DEFINITION_FILENAME),
        os.path.abspath(os.path.join(dags_path, DAG_DEFINITION_FILENAME)),
    )

    task_id = 'minimal_dockerized_dagster_airflow_node'
    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    pipeline_name = pipeline.name

    # for step in
    # res = subprocess.check_output(
    #     ['airflow', 'test', pipeline_name, task_id, execution_date]
    # )
