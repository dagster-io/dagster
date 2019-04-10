import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineConfigEvaluationError,
    PipelineDefinition,
    SolidInstance,
    execute_pipeline,
    solid,
    types,
)


def test_string_from_inputs():
    called = {}

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_context, string_input):
        assert string_input == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(name='test_string_from_inputs_pipeline', solids=[str_as_input])

    result = execute_pipeline(
        pipeline, {'solids': {'str_as_input': {'inputs': {'string_input': {'value': 'foo'}}}}}
    )

    assert result.success
    assert called['yup']


def test_string_from_aliased_inputs():
    called = {}

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_context, string_input):
        assert string_input == 'foo'
        called['yup'] = True

    pipeline = PipelineDefinition(
        solids=[str_as_input], dependencies={SolidInstance('str_as_input', alias='aliased'): {}}
    )

    result = execute_pipeline(
        pipeline, {'solids': {'aliased': {'inputs': {'string_input': {'value': 'foo'}}}}}
    )

    assert result.success
    assert called['yup']


def test_string_missing_inputs():
    called = {}

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_context, string_input):  # pylint: disable=W0613
        called['yup'] = True

    pipeline = PipelineDefinition(name='missing_inputs', solids=[str_as_input])
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(pipeline)

    assert len(exc_info.value.errors) == 1

    assert exc_info.value.errors[0].message == (
        '''Missing required field "solids" at document config root. '''
        '''Available Fields: "['context', 'execution', 'expectations', '''
        ''''solids', 'storage']".'''
    )

    assert 'yup' not in called


def test_string_missing_input_collision():
    called = {}

    @solid(outputs=[OutputDefinition(types.String)])
    def str_as_output(_context):
        return 'bar'

    @solid(inputs=[InputDefinition('string_input', types.String)])
    def str_as_input(_context, string_input):  # pylint: disable=W0613
        called['yup'] = True

    pipeline = PipelineDefinition(
        name='overlapping',
        solids=[str_as_input, str_as_output],
        dependencies={'str_as_input': {'string_input': DependencyDefinition('str_as_output')}},
    )
    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            pipeline, {'solids': {'str_as_input': {'inputs': {'string_input': 'bar'}}}}
        )

    assert 'Error 1: Undefined field "inputs" at path root:solids:str_as_input' in str(
        exc_info.value
    )

    assert 'yup' not in called
