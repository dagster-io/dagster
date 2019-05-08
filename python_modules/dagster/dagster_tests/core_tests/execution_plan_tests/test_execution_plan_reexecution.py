import uuid

import pytest

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

from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
    DagsterStepOutputNotFoundError,
)
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.execution_context import ReexecutionConfig
from dagster.core.intermediates_manager import StepOutputHandle
from dagster.core.object_store import get_filesystem_intermediate
from dagster.core.events import get_step_output_event


def define_addy_pipeline():
    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    pipeline_def = PipelineDefinition(
        name='execution_plan_reexecution',
        solids=[add_one, add_two, add_three],
        dependencies={
            'add_two': {'num': DependencyDefinition('add_one')},
            'add_three': {'num': DependencyDefinition('add_two')},
        },
    )
    return pipeline_def


def test_execution_plan_reexecution():
    pipeline_def = define_addy_pipeline()

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

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

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


def test_execution_plan_wrong_run_id():
    pipeline_def = define_addy_pipeline()

    unrun_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    with pytest.raises(DagsterRunNotFoundError) as exc_info:
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(
                storage_mode=RunStorageMode.FILESYSTEM,
                reexecution_config=ReexecutionConfig(
                    previous_run_id=unrun_id,
                    step_output_handles=[StepOutputHandle('add_one.transform')],
                ),
            ),
        )

    assert str(
        exc_info.value
    ) == 'Run id {} set as previous run id was not found in run storage'.format(unrun_id)

    assert exc_info.value.invalid_run_id == unrun_id


def test_execution_plan_wrong_invalid_step_key():
    pipeline_def = define_addy_pipeline()

    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM, run_id=old_run_id),
    )

    new_run_id = str(uuid.uuid4())

    run_config = RunConfig(
        run_id=new_run_id,
        reexecution_config=ReexecutionConfig(
            previous_run_id=result.run_id,
            step_output_handles=[StepOutputHandle('not_valid.transform')],
        ),
        storage_mode=RunStorageMode.FILESYSTEM,
    )

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=run_config,
            step_keys_to_execute=['add_two.transform'],
        )

    assert str(exc_info.value) == (
        'Step not_valid.transform was specified as a step from a previous run. '
        'It does not exist.'
    )


def test_execution_plan_wrong_invalid_output_name():
    pipeline_def = define_addy_pipeline()

    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM, run_id=old_run_id),
    )

    new_run_id = str(uuid.uuid4())

    run_config = RunConfig(
        run_id=new_run_id,
        reexecution_config=ReexecutionConfig(
            previous_run_id=result.run_id,
            step_output_handles=[StepOutputHandle('add_one.transform', 'not_an_output')],
        ),
        storage_mode=RunStorageMode.FILESYSTEM,
    )

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    with pytest.raises(DagsterStepOutputNotFoundError) as exc_info:
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=run_config,
            step_keys_to_execute=['add_two.transform'],
        )

    assert str(exc_info.value) == (
        'You specified a step_output_handle in the ReexecutionConfig that does not exist: '
        'Step add_one.transform does not have output not_an_output.'
    )

    assert exc_info.value.step_key == 'add_one.transform'
    assert exc_info.value.output_name == 'not_an_output'


def test_execution_plan_reexecution_with_in_memory():
    pipeline_def = define_addy_pipeline()

    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.IN_MEMORY, run_id=old_run_id),
    )

    assert result.success

    ## re-execute add_two

    new_run_id = str(uuid.uuid4())

    in_memory_run_config = RunConfig(
        run_id=new_run_id,
        reexecution_config=ReexecutionConfig(
            previous_run_id=result.run_id,
            step_output_handles=[StepOutputHandle('add_one.transform')],
        ),
        storage_mode=RunStorageMode.IN_MEMORY,
    )

    execution_plan = create_execution_plan(pipeline_def, environment_dict=environment_dict)

    with pytest.raises(DagsterInvariantViolationError):
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=in_memory_run_config,
            step_keys_to_execute=['add_two.transform'],
        )


def test_pipeline_step_key_subset_execution():
    pipeline_def = define_addy_pipeline()

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

    pipeline_reexecution_result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(
            run_id=new_run_id,
            reexecution_config=ReexecutionConfig(
                previous_run_id=result.run_id,
                step_output_handles=[StepOutputHandle('add_one.transform')],
            ),
            storage_mode=RunStorageMode.FILESYSTEM,
            step_keys_to_execute=['add_two.transform'],
        ),
    )

    assert pipeline_reexecution_result.success

    step_events = pipeline_reexecution_result.step_event_list
    assert step_events

    assert get_filesystem_intermediate(new_run_id, 'add_one.transform', Int) == 4
    assert get_filesystem_intermediate(new_run_id, 'add_two.transform', Int) == 6

    assert not get_step_output_event(step_events, 'add_one.transform')
    assert get_step_output_event(step_events, 'add_two.transform')


def test_pipeline_step_key_subset_execution_wrong_step_key_in_subset():
    pipeline_def = define_addy_pipeline()
    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM, run_id=old_run_id),
    )
    assert result.success

    new_run_id = str(uuid.uuid4())

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_pipeline(
            pipeline_def,
            environment_dict=environment_dict,
            run_config=RunConfig(
                run_id=new_run_id,
                reexecution_config=ReexecutionConfig(
                    previous_run_id=result.run_id,
                    step_output_handles=[StepOutputHandle('add_one.transform')],
                ),
                storage_mode=RunStorageMode.FILESYSTEM,
                step_keys_to_execute=['nope'],
            ),
        )


def test_pipeline_step_key_subset_execution_wrong_step_key_in_step_output_handles():
    pipeline_def = define_addy_pipeline()
    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM, run_id=old_run_id),
    )
    assert result.success

    new_run_id = str(uuid.uuid4())

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_pipeline(
            pipeline_def,
            environment_dict=environment_dict,
            run_config=RunConfig(
                run_id=new_run_id,
                reexecution_config=ReexecutionConfig(
                    previous_run_id=result.run_id,
                    step_output_handles=[StepOutputHandle('invalid_in_step_output_handles')],
                ),
                storage_mode=RunStorageMode.FILESYSTEM,
                step_keys_to_execute=['add_two.transform'],
            ),
        )


def test_pipeline_step_key_subset_execution_wrong_output_name_in_step_output_handles():
    pipeline_def = define_addy_pipeline()
    old_run_id = str(uuid.uuid4())
    environment_dict = {'solids': {'add_one': {'inputs': {'num': {'value': 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        environment_dict=environment_dict,
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM, run_id=old_run_id),
    )
    assert result.success

    new_run_id = str(uuid.uuid4())

    with pytest.raises(DagsterStepOutputNotFoundError):
        execute_pipeline(
            pipeline_def,
            environment_dict=environment_dict,
            run_config=RunConfig(
                run_id=new_run_id,
                reexecution_config=ReexecutionConfig(
                    previous_run_id=result.run_id,
                    step_output_handles=[StepOutputHandle('add_one.transform', 'invalid_output')],
                ),
                storage_mode=RunStorageMode.FILESYSTEM,
                step_keys_to_execute=['add_two.transform'],
            ),
        )
