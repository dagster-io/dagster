import datetime
import os
import shutil
import subprocess

from dagster.core.execution import create_execution_plan
from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow import scaffold_airflow_dag
from dagster_airflow.scaffold import _key_for_marshalled_result, _normalize_key

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

    shutil.copyfile(
        script_relative_path(static_path),
        os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))),
    )

    shutil.copyfile(
        script_relative_path(editable_path),
        os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))),
    )

    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    pipeline_name = pipeline.name

    execution_plan = create_execution_plan(pipeline, env_config)

    for step in execution_plan.topological_steps():
        task_id = _normalize_key(step.key)
        res = subprocess.check_output(['airflow', 'test', pipeline_name, task_id, execution_date])

        assert 'EXECUTION_PLAN_STEP_SUCCESS' in str(res)

        for step_output in step.step_outputs:
            assert 'for output {output_name}'.format(output_name=step_output.name) in str(res)

            assert os.path.isfile(_key_for_marshalled_result(step.key, step_output.name))
