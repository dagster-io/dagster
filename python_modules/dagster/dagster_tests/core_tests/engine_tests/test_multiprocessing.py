from dagster import (
    DependencyDefinition,
    ExecutionTargetHandle,
    InputDefinition,
    PipelineDefinition,
    PresetDefinition,
    execute_pipeline,
    execute_pipeline_with_preset,
    lambda_solid,
)
from dagster.core.instance import DagsterInstance


def test_diamond_simple_execution():
    result = execute_pipeline(define_diamond_pipeline())
    assert result.success
    assert result.result_for_solid('adder').output_value() == 11


def compute_event(result, solid_name):
    return result.result_for_solid(solid_name).compute_step_events[0]


def test_diamond_multi_execution():
    pipeline = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_diamond_pipeline'
    ).build_pipeline_definition()
    result = execute_pipeline(
        pipeline,
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

    return PipelineDefinition(
        name='diamond_execution',
        solid_defs=[return_two, add_three, mult_three, adder],
        dependencies={
            'add_three': {'num': DependencyDefinition('return_two')},
            'mult_three': {'num': DependencyDefinition('return_two')},
            'adder': {
                'left': DependencyDefinition('add_three'),
                'right': DependencyDefinition('mult_three'),
            },
        },
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


def define_error_pipeline():
    @lambda_solid
    def throw_error():
        raise Exception('bad programmer')

    return PipelineDefinition(name='error_pipeline', solid_defs=[throw_error])


def test_error_pipeline():
    pipeline = define_error_pipeline()
    result = execute_pipeline(pipeline, raise_on_error=False)
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


def test_solid_subset():
    pipeline = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'define_diamond_pipeline'
    ).build_pipeline_definition()

    result = execute_pipeline_with_preset(
        pipeline, 'just_adder', instance=DagsterInstance.local_temp(),
    )

    assert result.success

    assert result.result_for_solid('adder').output_value() == 2
