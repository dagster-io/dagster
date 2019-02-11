import datetime
import os
import subprocess

from airflow.models import TaskInstance

from dagster_airflow.scaffold import _key_for_marshalled_result, _normalize_key

from .utils import import_module_from_path


def test_unit_run_airflow_dag_steps(scaffold_dag):
    '''This test runs the steps in the sample Airflow DAG using the ``airflow test`` API.'''

    pipeline_name, execution_plan, execution_date, _s, _e = scaffold_dag

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
    _n, _p, _d, _s, editable_path = scaffold_dag

    execution_date = datetime.datetime.utcnow()

    test_dag = import_module_from_path('test_dag', editable_path)

    _dag, tasks = test_dag.make_dag(
        dag_id=test_dag.DAG_ID,
        dag_description=test_dag.DAG_DESCRIPTION,
        dag_kwargs=dict(default_args=test_dag.DEFAULT_ARGS, **test_dag.DAG_KWARGS),
        s3_conn_id=test_dag.S3_CONN_ID,
        modified_docker_operator_kwargs=test_dag.MODIFIED_DOCKER_OPERATOR_KWARGS,
        host_tmp_dir=test_dag.HOST_TMP_DIR,
    )

    # These are in topo order already
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        task.execute(context)
