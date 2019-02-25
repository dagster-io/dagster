import datetime
import os
import subprocess

import pytest

from airflow.models import TaskInstance

from dagster_airflow.scaffold import _key_for_marshalled_result, _normalize_key

from .utils import import_module_from_path


def test_run_airflow_dag(scaffold_dag):
    '''This test runs the sample Airflow dag using the TaskInstance API, directly from Python'''
    _n, _p, _d, static_path, editable_path = scaffold_dag

    execution_date = datetime.datetime.utcnow()

    import_module_from_path('demo_pipeline_static__scaffold', static_path)
    demo_pipeline = import_module_from_path('demo_pipeline', editable_path)

    _dag, tasks = demo_pipeline.make_dag(
        dag_id=demo_pipeline.DAG_ID,
        dag_description=demo_pipeline.DAG_DESCRIPTION,
        dag_kwargs=dict(default_args=demo_pipeline.DEFAULT_ARGS, **demo_pipeline.DAG_KWARGS),
        s3_conn_id=demo_pipeline.S3_CONN_ID,
        modified_docker_operator_kwargs=demo_pipeline.MODIFIED_DOCKER_OPERATOR_KWARGS,
        host_tmp_dir=demo_pipeline.HOST_TMP_DIR,
    )

    # These are in topo order already
    for task in tasks:
        ti = TaskInstance(task=task, execution_date=execution_date)
        context = ti.get_template_context()
        task.execute(context)
