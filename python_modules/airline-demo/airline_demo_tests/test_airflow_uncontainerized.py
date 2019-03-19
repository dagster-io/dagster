from collections import defaultdict

from dagster.core.execute_marshalling import execute_marshalling, MarshalledOutput
from dagster.core.execution import RunConfig, yield_pipeline_execution_context
from dagster.core.execution_plan import create_execution_plan_core
from dagster.utils import load_yaml_from_glob_list, mkdir_p, script_relative_path

try:
    from dagster_airflow.scaffold import _key_for_marshalled_result, coalesce_execution_steps
except ImportError:
    pass

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import airflow


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
    def test_uncontainerized_download_dag_execution_with_airflow_config(self, clean_results_dir):
        pipeline = define_airline_demo_download_pipeline()
        config_object = load_yaml_from_glob_list(
            [
                script_relative_path('../environments/airflow_base.yml'),
                script_relative_path('../environments/local_fast_download.yml'),
            ]
        )

        _uncontainerized_pipeline_execute(pipeline, config_object)

    @airflow
    def test_uncontainerized_ingest_dag_execution_with_airflow_config(self, clean_results_dir):
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
    def test_uncontainerized_warehouse_dag_execution_with_airflow_config(self, clean_results_dir):
        pipeline = define_airline_demo_warehouse_pipeline()
        config_object = load_yaml_from_glob_list(
            [
                script_relative_path('../environments/airflow_base.yml'),
                script_relative_path('../environments/local_warehouse.yml'),
            ]
        )

        _uncontainerized_pipeline_execute(pipeline, config_object)
