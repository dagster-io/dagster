import datetime
import itertools
import logging
import os

from collections import defaultdict

try:
    from airflow.models import TaskInstance
except ImportError:
    pass

from dagster import RunConfig
from dagster.core.execute_marshalling import execute_marshalling, MarshalledOutput
from dagster.core.execution import yield_pipeline_execution_context
from dagster.core.execution_plan import create_execution_plan_core
from dagster.utils import load_yaml_from_glob_list, mkdir_p, script_relative_path

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

try:
    from dagster_airflow.scaffold import _key_for_marshalled_result, coalesce_execution_steps
except ImportError:
    pass

from .marks import airflow
from .utils import import_module_from_path


def _uncontainerized_pipeline_execute(pipeline, config_object):
    with yield_pipeline_execution_context(pipeline, config_object, RunConfig()) as pipeline_context:
        execution_plan = create_execution_plan_core(pipeline_context)

    execution_steps = coalesce_execution_steps(execution_plan)

    for (_, solid_steps) in execution_steps:
        step_output_keys = set([])
        for step in solid_steps:
            for step_output in step.step_outputs:
                step_output_keys.add((step.key, step_output.name))

        # this is a nested dict of step_key -> input_name -> marshalling_key
        inputs_to_marshal = defaultdict(lambda: defaultdict(dict))

        for step in solid_steps:
            for step_input in step.step_inputs:
                step_input_key = (
                    step_input.prev_output_handle.step_key,
                    step_input.prev_output_handle.output_name,
                )
                if step_input_key in step_output_keys:
                    continue

                inputs_to_marshal[step.key][step_input.name] = _key_for_marshalled_result(
                    *step_input_key, prepend_run_id=False
                ).format(tmp='/tmp/results/', sep='')

        # this is a dict of step_key -> [MarshalledOutput]
        outputs_to_marshal = defaultdict(list)

        for step in solid_steps:
            for step_output in step.step_outputs:
                outputs_to_marshal[step.key].append(
                    MarshalledOutput(
                        step_output.name,
                        _key_for_marshalled_result(
                            step.key, step_output.name, prepend_run_id=False
                        ).format(tmp='/tmp/results/', sep=''),
                    )
                )

        step_keys = [step.key for step in solid_steps]

        # this is [ExecutionStepEvent(event_type=ExecutionStepEventType.STEP_OUTPUT)]
        result = execute_marshalling(
            pipeline,
            step_keys,
            inputs_to_marshal=inputs_to_marshal,
            outputs_to_marshal=outputs_to_marshal,
            environment_dict=config_object,
        )

        for execution_step_event in result:
            assert execution_step_event.step_failure_data is None
            key = _key_for_marshalled_result(
                execution_step_event.step_key,
                execution_step_event.step_output_data.output_name,
                prepend_run_id=False,
            ).format(tmp='/tmp/results/', sep='')


####################################################################################################
# These tests are "uncontainerized" because they simulate (to greater or lesser fidelity) the
# execution of containerized Airflow DAG nodes, but without the roundtrip through the Airflow and
# Docker machinery


class TestUncontainerizedDagExecution:
    @airflow
    def test_uncontainerized_download_dag_execution_with_airflow_config(clean_results_dir):
        pipeline = define_airline_demo_download_pipeline()
        config_object = load_yaml_from_glob_list(
            [
                script_relative_path('../environments/airflow_base.yml'),
                script_relative_path('../environments/local_fast_download.yml'),
            ]
        )

        _uncontainerized_pipeline_execute(pipeline, config_object)

    @airflow
    def test_uncontainerized_ingest_dag_execution_with_airflow_config(clean_results_dir):
        mkdir_p('/tmp/results')
        pipeline = define_airline_demo_ingest_pipeline()
        config_object = load_yaml_from_glob_list(
            [
                script_relative_path('../environments/airflow_base.yml'),
                script_relative_path('../environments/local_ingest.yml'),
            ]
        )

        _uncontainerized_pipeline_execute(pipeline, config_object)

    @airflow
    def test_uncontainerized_warehouse_dag_execution_with_airflow_config(clean_results_dir):
        pipeline = define_airline_demo_warehouse_pipeline()
        config_object = load_yaml_from_glob_list(
            [
                script_relative_path('../environments/airflow_base.yml'),
                script_relative_path('../environments/local_warehouse.yml'),
            ]
        )

        _uncontainerized_pipeline_execute(pipeline, config_object)


####################################################################################################
# These tests are "in-memory" because although they use the Airflow APIs to execute dockerized
# DAG nodes, they don't run through the full Airflow machinery (a separate scheduler and executor
# process, or even the single-node out-of-process invocation of `airflow test`)
@airflow
class TestInMemoryAirflow_0DownloadDagExecution:
    pipeline = define_airline_demo_download_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_download.yml')),
    ]

    def test_airflow_run_download_pipeline(self, scaffold_dag):
        _n, _p, _d, static_path, editable_path = scaffold_dag

        execution_date = datetime.datetime.utcnow()

        import_module_from_path('airline_demo_download_pipeline_static__scaffold', static_path)
        demo_pipeline = import_module_from_path('demo_pipeline', editable_path)

        _dag, tasks = demo_pipeline.make_dag(
            dag_id=demo_pipeline.DAG_ID,
            dag_description=demo_pipeline.DAG_DESCRIPTION,
            dag_kwargs=dict(default_args=demo_pipeline.DEFAULT_ARGS, **demo_pipeline.DAG_KWARGS),
            s3_conn_id=demo_pipeline.S3_CONN_ID,
            operator_kwargs={
                'persist_intermediate_results_to_s3': True,
                's3_bucket_name': 'dagster-lambda-execution',
                'network_mode': 'container:db',
            },
            host_tmp_dir=demo_pipeline.HOST_TMP_DIR,
        )

        # These are in topo order already
        for task in tasks:
            ti = TaskInstance(task=task, execution_date=execution_date)
            context = ti.get_template_context()
            task._log = logging  # pylint: disable=protected-access
            task.execute(context)


@airflow
class TestInMemoryAirflow_1IngestExecution:
    pipeline = define_airline_demo_ingest_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_ingest.yml')),
    ]

    def test_airflow_run_ingest_pipeline(self, scaffold_dag):
        _n, _p, _d, static_path, editable_path = scaffold_dag

        execution_date = datetime.datetime.utcnow()

        import_module_from_path('airline_demo_ingest_pipeline_static__scaffold', static_path)
        demo_pipeline = import_module_from_path('demo_pipeline', editable_path)

        _dag, tasks = demo_pipeline.make_dag(
            dag_id=demo_pipeline.DAG_ID,
            dag_description=demo_pipeline.DAG_DESCRIPTION,
            dag_kwargs=dict(default_args=demo_pipeline.DEFAULT_ARGS, **demo_pipeline.DAG_KWARGS),
            s3_conn_id=demo_pipeline.S3_CONN_ID,
            operator_kwargs={
                'persist_intermediate_results_to_s3': True,
                's3_bucket_name': 'dagster-lambda-execution',
                'network_mode': 'container:db',
            },
            host_tmp_dir=demo_pipeline.HOST_TMP_DIR,
        )

        # These are in topo order already
        for task in tasks:
            ti = TaskInstance(task=task, execution_date=execution_date)
            context = ti.get_template_context()
            task._log = logging  # pylint: disable=protected-access
            task.execute(context)


####################################################################################################
