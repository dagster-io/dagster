import datetime
import subprocess

from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow import scaffold_airflow_dag

from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


IMAGE = 'dagster-airflow-demo'


def test_unit_run_airflow_dag_steps(airflow_test, dags_path):
    pipeline = define_demo_execution_pipeline()
    env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

    static_path, editable_path = scaffold_airflow_dag(
        pipeline=pipeline,
        env_config=env_config,
        image=IMAGE,
        output_path=script_relative_path('test_project'),
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
    )

    # Ensure that the scaffolded files parse correctly
    subprocess.check_output(
        ['python', script_relative_path('test_project/demo_pipeline_editable__scaffold.py')]
    )
    # shutil.copyfile(
    #     script_relative_path(DAG_DEFINITION_FILENAME),
    #     os.path.abspath(os.path.join(dags_path, DAG_DEFINITION_FILENAME)),
    # )

    # task_id = 'minimal_dockerized_dagster_airflow_node'
    # execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    # pipeline_name = pipeline.name

    # # for step in
    # # res = subprocess.check_output(
    # #     ['airflow', 'test', pipeline_name, task_id, execution_date]
    # # )
