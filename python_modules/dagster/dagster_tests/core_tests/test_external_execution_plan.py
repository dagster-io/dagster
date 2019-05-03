import uuid

import pytest

from dagster import (
    DagsterExecutionStepNotFoundError,
    DagsterStepOutputNotFoundError,
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    RunConfig,
    lambda_solid,
)

from dagster.core.execution import (
    MultiprocessExecutorConfig,
    DagsterEventType,
    create_execution_plan,
    execute_plan,
)
from dagster.core.object_store import get_filesystem_intermediate, has_filesystem_intermediate


def define_inty_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception('whoops')

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solids=[return_one, add_one, user_throw_exception],
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

    assert execution_plan.get_step_by_key('return_one.transform')

    step_keys = ['return_one.transform']

    run_id = str(uuid.uuid4())

    return_one_step_events = list(
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(run_id=run_id),
            step_keys_to_execute=step_keys,
        )
    )

    assert get_step_output(return_one_step_events, 'return_one.transform')
    assert has_filesystem_intermediate(run_id, 'return_one.transform')
    assert get_filesystem_intermediate(run_id, 'return_one.transform', Int) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(run_id=run_id),
            step_keys_to_execute=['add_one.transform'],
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.transform')
    assert has_filesystem_intermediate(run_id, 'add_one.transform')
    assert get_filesystem_intermediate(run_id, 'add_one.transform', Int) == 2


def test_using_file_system_for_subplan_multiprocessing():
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)

    assert execution_plan.get_step_by_key('return_one.transform')

    step_keys = ['return_one.transform']

    run_id = str(uuid.uuid4())

    return_one_step_events = list(
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(
                run_id=run_id, executor_config=MultiprocessExecutorConfig(define_inty_pipeline)
            ),
            step_keys_to_execute=step_keys,
        )
    )

    assert get_step_output(return_one_step_events, 'return_one.transform')
    assert has_filesystem_intermediate(run_id, 'return_one.transform')
    assert get_filesystem_intermediate(run_id, 'return_one.transform', Int) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(
                run_id=run_id, executor_config=MultiprocessExecutorConfig(define_inty_pipeline)
            ),
            step_keys_to_execute=['add_one.transform'],
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.transform')
    assert has_filesystem_intermediate(run_id, 'add_one.transform')
    assert get_filesystem_intermediate(run_id, 'add_one.transform', Int) == 2


def test_execute_step_wrong_step_key():
    pipeline = define_inty_pipeline()

    execution_plan = create_execution_plan(pipeline)

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(execution_plan, step_keys_to_execute=['nope'])

    assert exc_info.value.step_key == 'nope'

    assert str(exc_info.value) == 'Execution plan does not contain step "nope"'


def test_using_file_system_for_subplan_missing_input():
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)

    run_id = str(uuid.uuid4())

    with pytest.raises(DagsterStepOutputNotFoundError):
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(run_id=run_id),
            step_keys_to_execute=['add_one.transform'],
        )


def test_using_file_system_for_subplan_invalid_step():
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'filesystem': {}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)

    run_id = str(uuid.uuid4())

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_plan(
            execution_plan,
            environment_dict=environment_dict,
            run_config=RunConfig(run_id=run_id),
            step_keys_to_execute=['nope'],
        )
