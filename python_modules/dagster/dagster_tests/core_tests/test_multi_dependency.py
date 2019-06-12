import pytest

from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    InputDefinition,
    Int,
    List,
    MultiDependencyDefinition,
    Nothing,
    OutputDefinition,
    PipelineDefinition,
    String,
    execute_pipeline,
    lambda_solid,
    solid,
)


def test_simple_values():
    @solid(inputs=[InputDefinition('numbers', List[Int])])
    def sum_num(_context, numbers):
        # cant guarantee order
        assert set(numbers) == set([1, 2, 3])
        return sum(numbers)

    @lambda_solid
    def emit_1():
        return 1

    @lambda_solid
    def emit_2():
        return 2

    @lambda_solid
    def emit_3():
        return 3

    result = execute_pipeline(
        PipelineDefinition(
            name='input_test',
            solids=[emit_1, emit_2, emit_3, sum_num],
            dependencies={
                'sum_num': {
                    'numbers': MultiDependencyDefinition(
                        [
                            DependencyDefinition('emit_1'),
                            DependencyDefinition('emit_2'),
                            DependencyDefinition('emit_3'),
                        ]
                    )
                }
            },
        )
    )
    assert result.success
    assert result.result_for_solid('sum_num').result_value() == 6


def test_interleaved_values():
    @solid(inputs=[InputDefinition('stuff', List[Any])])
    def collect(_context, stuff):
        assert set(stuff) == set([1, None, 'one'])
        return stuff

    @lambda_solid
    def emit_num():
        return 1

    @lambda_solid
    def emit_none():
        pass

    @lambda_solid
    def emit_str():
        return 'one'

    result = execute_pipeline(
        PipelineDefinition(
            name='input_test',
            solids=[emit_num, emit_none, emit_str, collect],
            dependencies={
                'collect': {
                    'stuff': MultiDependencyDefinition(
                        [
                            DependencyDefinition('emit_num'),
                            DependencyDefinition('emit_none'),
                            DependencyDefinition('emit_str'),
                        ]
                    )
                }
            },
        )
    )
    assert result.success


def test_nothing_deps():
    @solid(inputs=[InputDefinition('stuff', List[Any])])
    def collect(_context, stuff):
        return stuff

    @lambda_solid(output=OutputDefinition(Int))
    def emit_num():
        return 1

    @lambda_solid(output=OutputDefinition(Nothing))
    def emit_nothing():
        pass

    @lambda_solid(output=OutputDefinition(String))
    def emit_str():
        return 'one'

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r'Input "stuff" expects a value of type \[Any\] and output '
        '"result" returns type Nothing',
    ):
        PipelineDefinition(
            name='input_test',
            solids=[emit_num, emit_nothing, emit_str, collect],
            dependencies={
                'collect': {
                    'stuff': MultiDependencyDefinition(
                        [
                            DependencyDefinition('emit_num'),
                            DependencyDefinition('emit_nothing'),
                            DependencyDefinition('emit_str'),
                        ]
                    )
                }
            },
        )
