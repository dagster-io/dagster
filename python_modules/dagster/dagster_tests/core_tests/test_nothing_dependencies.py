from collections import defaultdict

import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DependencyDefinition,
    InputDefinition,
    Int,
    MultiDependencyDefinition,
    Nothing,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidInstance,
    execute_pipeline,
    lambda_solid,
    solid,
)


def _define_nothing_dep_pipeline():
    @lambda_solid(output=OutputDefinition(Nothing, 'complete'))
    def start_nothing():
        pass

    @lambda_solid(
        inputs=[
            InputDefinition('add_complete', Nothing),
            InputDefinition('yield_complete', Nothing),
        ]
    )
    def end_nothing():
        pass

    @lambda_solid(output=OutputDefinition(Int))
    def emit_value():
        return 1

    @lambda_solid(
        inputs=[InputDefinition('on_complete', Nothing), InputDefinition('num', Int)],
        output=OutputDefinition(Int),
    )
    def add_value(num):
        return 1 + num

    @solid(
        name='yield_values',
        inputs=[InputDefinition('on_complete', Nothing)],
        outputs=[
            OutputDefinition(Int, 'num_1'),
            OutputDefinition(Int, 'num_2'),
            OutputDefinition(Nothing, 'complete'),
        ],
    )
    def yield_values(_context):
        yield Result(1, 'num_1')
        yield Result(2, 'num_2')
        yield Result(None, 'complete')

    return PipelineDefinition(
        name='simple_exc',
        solids=[emit_value, add_value, start_nothing, end_nothing, yield_values],
        dependencies={
            'add_value': {
                'on_complete': DependencyDefinition('start_nothing', 'complete'),
                'num': DependencyDefinition('emit_value'),
            },
            'yield_values': {'on_complete': DependencyDefinition('start_nothing', 'complete')},
            'end_nothing': {
                'add_complete': DependencyDefinition('add_value'),
                'yield_complete': DependencyDefinition('yield_values', 'complete'),
            },
        },
    )


def test_valid_nothing_dependencies():

    result = execute_pipeline(_define_nothing_dep_pipeline())

    assert result.success


def test_invalid_input_dependency():
    @lambda_solid(output=OutputDefinition(Nothing))
    def do_nothing():
        pass

    @lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    with pytest.raises(DagsterInvalidDefinitionError):
        PipelineDefinition(
            name='bad_dep',
            solids=[do_nothing, add_one],
            dependencies={'add_one': {'num': DependencyDefinition('do_nothing')}},
        )


def test_result_type_check():
    @solid(outputs=[OutputDefinition(Nothing)])
    def bad(_context):
        yield Result('oops')

    pipeline = PipelineDefinition(name='fail', solids=[bad])
    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipeline)


def test_nothing_inputs():
    @lambda_solid(inputs=[InputDefinition('never_defined', Nothing)])
    def emit_one():
        return 1

    @lambda_solid
    def emit_two():
        return 2

    @lambda_solid
    def emit_three():
        return 3

    @lambda_solid(output=OutputDefinition(Nothing))
    def emit_nothing():
        pass

    @solid(
        inputs=[
            InputDefinition('_one', Nothing),
            InputDefinition('one', Int),
            InputDefinition('_two', Nothing),
            InputDefinition('two', Int),
            InputDefinition('_three', Nothing),
            InputDefinition('three', Int),
        ]
    )
    def adder(_context, one, two, three):
        assert one == 1
        assert two == 2
        assert three == 3
        return one + two + three

    pipeline = PipelineDefinition(
        name='input_test',
        solids=[emit_one, emit_two, emit_three, emit_nothing, adder],
        dependencies={
            SolidInstance('emit_nothing', '_one'): {},
            SolidInstance('emit_nothing', '_two'): {},
            SolidInstance('emit_nothing', '_three'): {},
            'adder': {
                '_one': DependencyDefinition('_one'),
                '_two': DependencyDefinition('_two'),
                '_three': DependencyDefinition('_three'),
                'one': DependencyDefinition('emit_one'),
                'two': DependencyDefinition('emit_two'),
                'three': DependencyDefinition('emit_three'),
            },
        },
    )
    result = execute_pipeline(pipeline)
    assert result.success


def test_fanin_deps():
    called = defaultdict(int)

    @lambda_solid
    def emit_two():
        return 2

    @lambda_solid(output=OutputDefinition(Nothing))
    def emit_nothing():
        called['emit_nothing'] += 1

    @solid(
        inputs=[
            InputDefinition('ready', Nothing),
            InputDefinition('num_1', Int),
            InputDefinition('num_2', Int),
        ]
    )
    def adder(_context, num_1, num_2):
        assert called['emit_nothing'] == 3
        called['adder'] += 1
        return num_1 + num_2

    pipeline = PipelineDefinition(
        name='input_test',
        solids=[emit_two, emit_nothing, adder],
        dependencies={
            SolidInstance('emit_two', 'emit_1'): {},
            SolidInstance('emit_two', 'emit_2'): {},
            SolidInstance('emit_nothing', '_one'): {},
            SolidInstance('emit_nothing', '_two'): {},
            SolidInstance('emit_nothing', '_three'): {},
            'adder': {
                'ready': MultiDependencyDefinition(
                    [
                        DependencyDefinition('_one'),
                        DependencyDefinition('_two'),
                        DependencyDefinition('_three'),
                    ]
                ),
                'num_1': DependencyDefinition('emit_1'),
                'num_2': DependencyDefinition('emit_2'),
            },
        },
    )
    result = execute_pipeline(pipeline)
    assert result.success
    assert called['adder'] == 1
    assert called['emit_nothing'] == 3


def test_invalid_fanin():
    @solid(inputs=[InputDefinition('num', Int)])
    def adder(_context, num):
        return num + 1

    @lambda_solid()
    def emit_nothing():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match='FanInDependency only supports type "Nothing"'
    ):
        PipelineDefinition(
            name='input_test',
            solids=[emit_nothing, adder],
            dependencies={
                SolidInstance('emit_nothing', '_one'): {},
                SolidInstance('emit_nothing', '_two'): {},
                'adder': {
                    'num': MultiDependencyDefinition(
                        [DependencyDefinition('_one'), DependencyDefinition('_two')]
                    )
                },
            },
        )
