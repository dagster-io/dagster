import os
import time

from dagster import (
    ExecutionTargetHandle,
    Field,
    InputDefinition,
    Nothing,
    OutputDefinition,
    PresetDefinition,
    String,
    execute_pipeline,
    execute_pipeline_with_preset,
    lambda_solid,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance


def test_diamond_simple_execution():
    result = execute_pipeline(define_diamond_pipeline())
    assert result.success
    assert result.result_for_solid('adder').output_value() == 11


def compute_event(result, solid_name):
    return result.result_for_solid(solid_name).compute_step_events[0]


def test_diamond_multi_execution():
    pipe = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_diamond_pipeline'
    ).build_pipeline_definition()
    result = execute_pipeline(
        pipe,
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
    )
    assert result.success

    assert result.result_for_solid('adder').output_value() == 11

    # https://github.com/dagster-io/dagster/issues/1875
    # pids_by_solid = {}
    # for solid in pipeline.solids:
    #     pids_by_solid[solid.name] = compute_event(result, solid.name).logging_tags['pid']

    # # guarantee that all solids ran in their own process
    # assert len(set(pids_by_solid.values())) == len(pipeline.solids)


def define_diamond_pipeline():
    @lambda_solid
    def return_two():
        return 2

    @lambda_solid(input_defs=[InputDefinition('num')])
    def add_three(num):
        return num + 3

    @lambda_solid(input_defs=[InputDefinition('num')])
    def mult_three(num):
        return num * 3

    @lambda_solid(input_defs=[InputDefinition('left'), InputDefinition('right')])
    def adder(left, right):
        return left + right

    @pipeline(
        preset_defs=[
            PresetDefinition(
                'just_adder',
                {
                    'storage': {'filesystem': {}},
                    'execution': {'multiprocess': {}},
                    'solids': {'adder': {'inputs': {'left': {'value': 1}, 'right': {'value': 1}}}},
                },
                solid_subset=['adder'],
            )
        ],
    )
    def diamond_pipeline():
        two = return_two()
        adder(left=add_three(two), right=mult_three(two))

    return diamond_pipeline


def define_error_pipeline():
    @lambda_solid
    def should_never_execute(_x):
        assert False  # this should never execute

    @lambda_solid
    def throw_error():
        raise Exception('bad programmer')

    @pipeline
    def error_pipeline():
        should_never_execute(throw_error())

    return error_pipeline


def test_error_pipeline():
    pipe = define_error_pipeline()
    result = execute_pipeline(pipe, raise_on_error=False)
    assert not result.success


def test_error_pipeline_multiprocess():
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_fn(define_error_pipeline).build_pipeline_definition(),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
    )
    assert not result.success


def test_mem_storage_error_pipeline_multiprocess():
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_fn(define_diamond_pipeline).build_pipeline_definition(),
        environment_dict={'execution': {'multiprocess': {}}},
        instance=DagsterInstance.local_temp(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure


def test_invalid_instance():
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_fn(define_diamond_pipeline).build_pipeline_definition(),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure
    assert (
        result.event_list[0].pipeline_init_failure_data.error.cls_name
        == 'DagsterUnmetExecutorRequirementsError'
    )
    assert 'non-ephemeral instance' in result.event_list[0].pipeline_init_failure_data.error.message


def test_no_handle():
    result = execute_pipeline(
        define_diamond_pipeline(),
        environment_dict={'storage': {'filesystem': {}}, 'execution': {'multiprocess': {}}},
        instance=DagsterInstance.ephemeral(),
        raise_on_error=False,
    )
    assert not result.success
    assert len(result.event_list) == 1
    assert result.event_list[0].is_failure
    assert (
        result.event_list[0].pipeline_init_failure_data.error.cls_name
        == 'DagsterUnmetExecutorRequirementsError'
    )
    assert 'ExecutionTargetHandle' in result.event_list[0].pipeline_init_failure_data.error.message


def test_solid_subset():
    pipe = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_diamond_pipeline'
    ).build_pipeline_definition()

    result = execute_pipeline_with_preset(
        pipe, 'just_adder', instance=DagsterInstance.local_temp(),
    )

    assert result.success

    assert result.result_for_solid('adder').output_value() == 2


def define_subdag_pipeline():
    @solid(config=Field(String))
    def waiter(context):
        done = False
        while not done:
            time.sleep(0.25)
            if os.path.isfile(context.solid_config):
                done = True
                time.sleep(1)

    @solid(
        input_defs=[InputDefinition('after', Nothing)],
        output_defs=[OutputDefinition(Nothing)],
        config=Field(String),
    )
    def counter(context):
        with open(context.solid_config, 'a') as fd:
            fd.write('1')
        return

    @pipeline
    def seperate():
        waiter()
        counter.alias('counter_3')(counter.alias('counter_2')(counter.alias('counter_1')()))

    return seperate


def test_seperate_sub_dags():
    pipe = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_subdag_pipeline'
    ).build_pipeline_definition()

    with seven.TemporaryDirectory() as tempdir:
        file_one = os.path.join(tempdir, 'foo_one')
        file_two = os.path.join(tempdir, 'foo_two')
        file_three = os.path.join(tempdir, 'foo_three')

        result = execute_pipeline(
            pipe,
            environment_dict={
                'storage': {'filesystem': {}},
                'execution': {'multiprocess': {'config': {'max_concurrent': 4}}},
                'solids': {
                    'waiter': {'config': file_three},
                    'counter_1': {'config': file_one},
                    'counter_2': {'config': file_two},
                    'counter_3': {'config': file_three},
                },
            },
            instance=DagsterInstance.local_temp(),
        )

    assert result.success
    # ensure that
    assert [
        str(event.solid_handle) for event in result.step_event_list if event.is_step_success
    ] == ['counter_1', 'counter_2', 'counter_3', 'waiter']
