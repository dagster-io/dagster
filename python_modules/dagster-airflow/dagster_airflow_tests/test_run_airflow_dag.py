import os
import subprocess

from dagster_airflow.scaffold import _key_for_marshalled_result, _normalize_key


def test_unit_run_airflow_dag_steps(scaffold_dag):
    '''This test runs the steps in the sample Airflow DAG using the ``airflow test`` API.'''

    pipeline_name, execution_plan, execution_date = scaffold_dag

    for step in execution_plan.topological_steps():
        task_id = _normalize_key(step.key)
        try:
            res = subprocess.check_output(
                ['airflow', 'test', pipeline_name, task_id, execution_date]
            )
        except subprocess.CalledProcessError as cpe:
            raise Exception('Process failed with output {}'.format(cpe.output))

        assert 'EXECUTION_PLAN_STEP_SUCCESS' in str(res)

        for step_output in step.step_outputs:
            assert os.path.isfile(_key_for_marshalled_result(step.key, step_output.name))


def test_run_airflow_dag(scaffold_dag):
    '''This test runs the sample Airflow dag using the '''

    pass
