import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
)
from dagster.core.events import get_step_output_event
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts


def env_with_fs(environment_dict):
    return merge_dicts(environment_dict, {'storage': {'filesystem': {}}})


def define_addy_pipeline():
    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    pipeline_def = PipelineDefinition(
        name='execution_plan_reexecution',
        solid_defs=[add_one, add_two, add_three],
        dependencies={
            'add_two': {'num': DependencyDefinition('add_one')},
            'add_three': {'num': DependencyDefinition('add_two')},
        },
    )
    return pipeline_def


def test_execution_plan_reexecution():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    old_run_id = make_new_run_id()
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(run_id=old_run_id),
        instance=instance,
    )

    assert result.success

    store = build_fs_intermediate_store(instance.intermediates_directory, result.run_id)
    assert store.get_intermediate(None, 'add_one.compute', Int).obj == 4
    assert store.get_intermediate(None, 'add_two.compute', Int).obj == 6

    ## re-execute add_two

    new_run_id = make_new_run_id()

    pipeline_run = PipelineRun(
        pipeline_name=pipeline_def.name,
        run_id=new_run_id,
        environment_dict=environment_dict,
        mode='default',
        previous_run_id=result.run_id,
    )

    execution_plan = create_execution_plan(
        pipeline_def, environment_dict=environment_dict, run_config=pipeline_run
    )

    step_events = execute_plan(
        execution_plan.build_subset_plan(['add_two.compute']),
        environment_dict=environment_dict,
        pipeline_run=pipeline_run,
        instance=instance,
    )

    store = build_fs_intermediate_store(instance.intermediates_directory, new_run_id)
    assert store.get_intermediate(None, 'add_one.compute', Int).obj == 4
    assert store.get_intermediate(None, 'add_two.compute', Int).obj == 6

    assert not get_step_output_event(step_events, 'add_one.compute')
    assert get_step_output_event(step_events, 'add_two.compute')


def test_execution_plan_wrong_run_id():
    pipeline_def = define_addy_pipeline()

    unrun_id = make_new_run_id()
    new_run_id = make_new_run_id()
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})

    pipeline_run = PipelineRun(
        pipeline_name=pipeline_def.name,
        run_id=new_run_id,
        environment_dict=environment_dict,
        mode='default',
        previous_run_id=unrun_id,
    )

    execution_plan = create_execution_plan(
        pipeline_def, environment_dict=environment_dict, run_config=pipeline_run
    )

    with pytest.raises(DagsterRunNotFoundError) as exc_info:
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=DagsterInstance.ephemeral(),
        )

    assert str(
        exc_info.value
    ) == 'Run id {} set as previous run id was not found in instance'.format(unrun_id)

    assert exc_info.value.invalid_run_id == unrun_id


def test_execution_plan_reexecution_with_in_memory():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    old_run_id = make_new_run_id()
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(run_id=old_run_id),
        instance=instance,
    )

    assert result.success

    ## re-execute add_two

    new_run_id = make_new_run_id()

    pipeline_run = PipelineRun(
        pipeline_name=pipeline_def.name,
        run_id=new_run_id,
        environment_dict=environment_dict,
        mode='default',
        previous_run_id=result.run_id,
    )

    execution_plan = create_execution_plan(
        pipeline_def, environment_dict=environment_dict, run_config=pipeline_run
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_plan(
            execution_plan.build_subset_plan(['add_two.compute']),
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
        )


def test_pipeline_step_key_subset_execution():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    old_run_id = make_new_run_id()
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(run_id=old_run_id),
        instance=instance,
    )

    assert result.success

    store = build_fs_intermediate_store(instance.intermediates_directory, result.run_id)
    assert store.get_intermediate(None, 'add_one.compute', Int).obj == 4
    assert store.get_intermediate(None, 'add_two.compute', Int).obj == 6

    ## re-execute add_two

    new_run_id = make_new_run_id()

    pipeline_reexecution_result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(
            run_id=new_run_id,
            previous_run_id=result.run_id,
            step_keys_to_execute=['add_two.compute'],
        ),
        instance=instance,
    )

    assert pipeline_reexecution_result.success

    step_events = pipeline_reexecution_result.step_event_list
    assert step_events

    store = build_fs_intermediate_store(instance.intermediates_directory, new_run_id)
    assert store.get_intermediate(None, 'add_one.compute', Int).obj == 4
    assert store.get_intermediate(None, 'add_two.compute', Int).obj == 6

    assert not get_step_output_event(step_events, 'add_one.compute')
    assert get_step_output_event(step_events, 'add_two.compute')


def test_pipeline_step_key_subset_execution_wrong_step_key_in_subset():
    pipeline_def = define_addy_pipeline()
    old_run_id = make_new_run_id()
    environment_dict = env_with_fs({'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}})
    result = execute_pipeline(
        pipeline_def, environment_dict=environment_dict, run_config=RunConfig(run_id=old_run_id)
    )
    assert result.success

    new_run_id = make_new_run_id()

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_pipeline(
            pipeline_def,
            environment_dict=environment_dict,
            run_config=RunConfig(
                run_id=new_run_id, previous_run_id=result.run_id, step_keys_to_execute=['nope']
            ),
        )
