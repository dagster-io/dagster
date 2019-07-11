import pytest

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    ExecutionTargetHandle,
    InProcessExecutorConfig,
    InputDefinition,
    MultiprocessExecutorConfig,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
    lambda_solid,
)


def test_diamond_simple_execution():
    result = execute_pipeline(
        define_diamond_pipeline(), run_config=RunConfig(executor_config=InProcessExecutorConfig())
    )
    assert result.success
    assert result.result_for_solid('adder').output_value() == 11


def compute_event(result, solid_name):
    return result.result_for_solid(solid_name).compute_step_events[0]


def test_diamond_multi_execution():
    pipeline = define_diamond_pipeline()
    result = execute_pipeline(
        pipeline,
        environment_dict={'storage': {'filesystem': {}}},
        run_config=RunConfig(
            executor_config=MultiprocessExecutorConfig(
                ExecutionTargetHandle.for_pipeline_fn(define_diamond_pipeline)
            )
        ),
    )
    assert result.success

    assert result.result_for_solid('adder').output_value() == 11

    pids_by_solid = {}
    for solid in pipeline.solids:
        pids_by_solid[solid.name] = compute_event(result, solid.name).logging_tags['pid']

    # guarantee that all solids ran in their own process
    assert len(set(pids_by_solid.values())) == len(pipeline.solids)


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
    )


def define_error_pipeline():
    @lambda_solid
    def throw_error():
        raise Exception('bad programmer')

    return PipelineDefinition(name='error_pipeline', solid_defs=[throw_error])


def test_error_pipeline():
    pipeline = define_error_pipeline()
    result = execute_pipeline(
        pipeline,
        run_config=RunConfig(executor_config=InProcessExecutorConfig(raise_on_error=False)),
    )
    assert not result.success


def test_error_pipeline_multiprocess():
    pipeline = define_error_pipeline()
    result = execute_pipeline(
        pipeline,
        run_config=RunConfig(
            executor_config=MultiprocessExecutorConfig(
                ExecutionTargetHandle.for_pipeline_fn(define_error_pipeline)
            )
        ),
        environment_dict={'storage': {'filesystem': {}}},
    )
    assert not result.success


def test_mem_storage_error_pipeline_multiprocess():
    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        execute_pipeline(
            define_diamond_pipeline(),
            run_config=RunConfig(
                executor_config=MultiprocessExecutorConfig(
                    ExecutionTargetHandle.for_pipeline_fn(define_error_pipeline)
                )
            ),
        )

    assert (
        'While invoking '
        'pipeline diamond_execution. You have attempted to use the '
        'multiprocessing executor while using system storage in_memory '
        'which does not persist intermediates. This means there would '
        'be no way to move data between different processes. Please '
        'configure your pipeline in the storage config section to use '
        'persistent system storage such as the filesystem.'
    ) in str(exc_info.value)
