import pytest

from dagster import (
    DagsterExecutionStepNotFoundError,
    DagsterStepOutputNotFoundError,
    DependencyDefinition,
    ExecutionTargetHandle,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)
from dagster.core.execution.api import DagsterEventType, create_execution_plan, execute_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.utils import make_new_run_id


def define_inty_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception('whoops')

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solid_defs=[return_one, add_one, user_throw_exception],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    return pipeline


def get_step_output(step_events, step_key, output_name='result'):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def test_using_file_system_for_subplan():
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)
    instance = DagsterInstance.ephemeral()
    assert execution_plan.get_step_by_key('return_one.compute')

    run_id = make_new_run_id()
    pipeline_run = PipelineRun.create_empty_run(pipeline.name, run_id)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(['return_one.compute']),
            instance,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
        )
    )

    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert get_step_output(return_one_step_events, 'return_one.compute')
    assert store.has_intermediate(None, 'return_one.compute')
    assert store.get_intermediate(None, 'return_one.compute', Int).obj == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(['add_one.compute']),
            instance,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.compute')
    assert store.has_intermediate(None, 'add_one.compute')
    assert store.get_intermediate(None, 'add_one.compute', Int).obj == 2


def test_using_file_system_for_subplan_multiprocessing():

    environment_dict = {'storage': {'filesystem': {}}}
    instance = DagsterInstance.local_temp()

    execution_plan = create_execution_plan(
        ExecutionTargetHandle.for_pipeline_fn(define_inty_pipeline).build_pipeline_definition(),
        environment_dict=environment_dict,
    )

    assert execution_plan.get_step_by_key('return_one.compute')

    run_id = make_new_run_id()
    run = instance.create_empty_run(run_id, execution_plan.pipeline_def.name)

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(['return_one.compute']),
            instance,
            environment_dict=dict(environment_dict, execution={'multiprocess': {}}),
            pipeline_run=run,
        )
    )

    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)

    assert get_step_output(return_one_step_events, 'return_one.compute')
    assert store.has_intermediate(None, 'return_one.compute')
    assert store.get_intermediate(None, 'return_one.compute', Int).obj == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(['add_one.compute']),
            instance,
            environment_dict=dict(environment_dict, execution={'multiprocess': {}}),
            pipeline_run=run,
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.compute')
    assert store.has_intermediate(None, 'add_one.compute')
    assert store.get_intermediate(None, 'add_one.compute', Int).obj == 2


def test_execute_step_wrong_step_key():
    pipeline = define_inty_pipeline()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline)
    pipeline_run = PipelineRun.create_empty_run(pipeline.name, make_new_run_id())

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(['nope']), instance, pipeline_run=pipeline_run
        )

    assert exc_info.value.step_keys == ['nope']

    assert str(exc_info.value) == 'Execution plan does not contain step: nope'

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(['nope', 'nuh_uh']),
            instance,
            pipeline_run=pipeline_run,
        )

    assert exc_info.value.step_keys == ['nope', 'nuh_uh']

    assert str(exc_info.value) == 'Execution plan does not contain steps: nope, nuh_uh'


def test_using_file_system_for_subplan_missing_input():
    pipeline = define_inty_pipeline()
    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)
    pipeline_run = PipelineRun.create_empty_run(pipeline.name, make_new_run_id())

    with pytest.raises(DagsterStepOutputNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(['add_one.compute']),
            DagsterInstance.ephemeral(),
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
        )


def test_using_file_system_for_subplan_invalid_step():
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)
    pipeline_run = PipelineRun.create_empty_run(pipeline.name, make_new_run_id())

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(['nope']),
            DagsterInstance.ephemeral(),
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
        )
