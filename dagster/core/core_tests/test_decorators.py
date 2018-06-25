import pytest
from dagster import config
from dagster import check
from dagster.core import types
from dagster.core.definitions import OutputDefinition, InputDefinition
from dagster.core.decorators import solid, source, materialization, with_context
from dagster.core.execution import (
    output_single_solid, execute_single_solid, DagsterExecutionContext,
    create_single_solid_env_from_arg_dicts
)


def create_test_context():
    return DagsterExecutionContext()


def create_test_env(env_config=None):
    if not env_config:
        env_config = {
            'environment': {
                'inputs': [],
            }
        }
    return config.Environment(
        input_sources=[
            config.Input(input_name=s['input_name'], args=s['args'], source=s['source'])
            for s in check.list_elem(env_config['environment'], 'inputs')
        ]
    )


def test_solid():
    @solid()
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_test_env(),
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_solid_with_name():
    @solid(name="foobar")
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_test_env(),
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_solid_with_context():
    @solid(name="foobar")
    @with_context
    def hello_world(context):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_test_env(),
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_solid_with_input():
    @source(name="TEST", argument_def_dict={'foo': types.STRING})
    def test_source(args):
        return {'foo': args['foo']}

    @solid(inputs=[InputDefinition(name="i", sources=[test_source])])
    def hello_world(i):
        return i

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_test_env(
            {
                'environment': {
                    'inputs': [
                        {
                            'input_name': 'i',
                            'source': 'TEST',
                            'args': {
                                'foo': 'bar',
                            },
                        },
                    ]
                }
            }
        )
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_sources():
    @source(name="WITH_CONTEXT", argument_def_dict={'foo': types.STRING})
    @with_context
    def context_source(context, args):
        return {'foo': args['foo']}

    @source(name="NO_CONTEXT", argument_def_dict={'foo': types.STRING})
    def no_context_source(args):
        return {'foo': args['foo']}

    @solid(inputs=[InputDefinition(name="i", sources=[context_source, no_context_source])])
    def hello_world(i):
        return i

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_test_env(
            {
                'environment': {
                    'inputs': [
                        {
                            'input_name': 'i',
                            'source': 'NO_CONTEXT',
                            'args': {
                                'foo': 'bar',
                            },
                        },
                    ]
                }
            }
        )
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_test_env(
            {
                'environment': {
                    'inputs': [
                        {
                            'input_name': 'i',
                            'source': 'WITH_CONTEXT',
                            'args': {
                                'foo': 'bar',
                            },
                        },
                    ]
                }
            }
        )
    )

    assert result.success

    assert result.transformed_value['foo'] == 'bar'


def test_materializations():
    test_output = {}

    @materialization(name="CONTEXT")
    @with_context
    def materialization_with_context(context, args, data):
        test_output['test'] = data

    @materialization(name="NO_CONTEXT")
    def materialization_no_context(args, data):
        test_output['test'] = data

    @solid(
        output=OutputDefinition(
            materializations=[materialization_with_context, materialization_no_context]
        )
    )
    def hello():
        return {'foo': 'bar'}

    output_single_solid(
        create_test_context(),
        hello,
        environment=create_single_solid_env_from_arg_dicts(hello, {}),
        materialization_type='CONTEXT',
        arg_dict={}
    )

    assert test_output['test'] == {'foo': 'bar'}

    test_output = {}

    output_single_solid(
        create_test_context(),
        hello,
        environment=create_single_solid_env_from_arg_dicts(hello, {}),
        materialization_type='NO_CONTEXT',
        arg_dict={}
    )

    assert test_output['test'] == {'foo': 'bar'}
