import datetime
import os

from airflow.models import TaskInstance

from dagster.utils import script_relative_path

from airline_demo.pipelines import define_airline_demo_download_pipeline

from .utils import import_module_from_path


class TestInMemoryAirflowDagExecution:
    pipeline = define_airline_demo_download_pipeline
    config = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_download.yml')),
    ]

    def test_airflow_run_download_pipeline(self, scaffold_dag):
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
