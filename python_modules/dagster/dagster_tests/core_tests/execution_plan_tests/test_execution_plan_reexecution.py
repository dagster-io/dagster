import uuid

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    RunConfig,
    RunStorageMode,
)

from dagster.core.execution import create_execution_plan, execute_plan
from dagster.core.intermediates_manager import StepOutputHandle
from dagster.core.execution_context import ReexecutionConfig
from dagster.core.object_store import get_filesystem_intermediate
from dagster.core.execution_plan.objects import get_step_output_event


def test_execution_plan_reexecution():
    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    pipeline_def = PipelineDefinition(
        name='execution_plan_reexecution',
        solids=[add_one, add_two],
        dependencies={'add_two': {'num': DependencyDefinition('add_one')}},
    )

    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM, run_id=old_run_id),
    )

    assert result.success
    assert get_filesystem_intermediate(result.run_id, 'add_one.transform', Int) == 4
    assert get_filesystem_intermediate(result.run_id, 'add_two.transform', Int) == 6

    ## re-execute add_two

    new_run_id = str(uuid.uuid4())

    run_config = RunConfig(
        run_id=new_run_id,
        reexecution_config=ReexecutionConfig(
            previous_run_id=result.run_id,
            step_output_handles=[StepOutputHandle('add_one.transform')],
        ),
        storage_mode=RunStorageMode.FILESYSTEM,
    )

    execution_plan = create_execution_plan(
        pipeline_def, environment_dict=environment_dict, run_config=run_config
    )

    step_events = execute_plan(
        execution_plan,
        environment_dict=environment_dict,
        run_config=run_config,
        step_keys_to_execute=['add_two.transform'],
    )

    assert get_filesystem_intermediate(new_run_id, 'add_one.transform', Int) == 4
    assert get_filesystem_intermediate(new_run_id, 'add_two.transform', Int) == 6

    assert not get_step_output_event(step_events, 'add_one.transform')
    assert get_step_output_event(step_events, 'add_two.transform')
