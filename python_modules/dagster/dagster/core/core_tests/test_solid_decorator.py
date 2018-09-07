import pytest

from dagster import (
    ConfigDefinition,
    DagsterTypeError,
    ExecutionContext,
    Field,
    OutputDefinition,
    Result,
    config,
    solid,
    types,
)

from dagster.core.test_utils import execute_single_solid


def _execute_empty(solid_inst):
    execute_single_solid(
        ExecutionContext(),
        solid_inst,
        config.Environment(),
    )


def test_solid_no_parens():
    called = {}

    @solid
    def hello_world(_context, _inputs, _conf):
        called['yep'] = True

    pipeline_result = execute_single_solid(
        ExecutionContext(),
        hello_world,
        config.Environment(),
    )

    assert pipeline_result.success
    assert called['yep']


def test_solid_no_args():
    called = {}

    @solid()
    def hello_world(_context, _inputs, _conf):
        called['yep'] = True

    pipeline_result = execute_single_solid(
        ExecutionContext(),
        hello_world,
        config.Environment(),
    )

    assert pipeline_result.success
    assert called['yep']


def test_solid():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_context, _inputs, _conf):
        return {'foo': 'bar'}

    pipeline_result = execute_single_solid(
        ExecutionContext(),
        hello_world,
        config.Environment(),
    )

    assert pipeline_result.success
    assert len(pipeline_result.result_list) == 1
    result = pipeline_result.result_for_solid('hello_world')
    assert result.transformed_value()['foo'] == 'bar'


def test_solid_yield():
    @solid(output=OutputDefinition())
    def hello_world(_context, _inputs, _conf):
        yield Result(value={'foo': 'bar'})

    pipeline_result = execute_single_solid(
        ExecutionContext(),
        hello_world,
        config.Environment(),
    )

    assert pipeline_result.success
    assert len(pipeline_result.result_list) == 1
    result = pipeline_result.result_for_solid('hello_world')
    assert result.transformed_value()['foo'] == 'bar'


def test_solid_context():
    test_context = ExecutionContext()

    called = {}

    @solid
    def hello_world(context, _inputs, _conf):
        called['yep'] = True
        assert context == test_context

    pipeline_result = execute_single_solid(
        test_context,
        hello_world,
        config.Environment(),
    )

    assert called['yep']

    assert pipeline_result.success


def test_solid_with_any_config():
    config_value = {'sdjkfd': 'ksjdkfdj'}
    called = {}

    @solid
    def hello_world(_context, _inputs, conf):
        called['yep'] = True
        assert conf == config_value

    pipeline_result = execute_single_solid(
        ExecutionContext(),
        hello_world,
        config.Environment(solids={'hello_world': config.Solid(config_value)})
    )

    assert pipeline_result.success


def test_solid_with_defined_config():
    config_value = {'config_key': 'config_value'}
    called = {}

    @solid(config_def=ConfigDefinition(types.ConfigDictionary({'config_key': Field(types.String)})))
    def hello_world(_context, _inputs, conf):
        called['yep'] = True
        assert conf == config_value

    pipeline_result = execute_single_solid(
        ExecutionContext(),
        hello_world,
        config.Environment(solids={'hello_world': config.Solid(config_value)})
    )

    assert pipeline_result.success


def test_solid_with_defined_config_error():
    @solid(config_def=ConfigDefinition(types.ConfigDictionary({'config_key': Field(types.String)})))
    def hello_world(_context, _inputs, _conf):
        pass

    with pytest.raises(DagsterTypeError):
        execute_single_solid(
            ExecutionContext(),
            hello_world,
            config.Environment(solids={'hello_world': config.Solid({
                'kdjfkdjkfd': 'foo'
            })})
        )
