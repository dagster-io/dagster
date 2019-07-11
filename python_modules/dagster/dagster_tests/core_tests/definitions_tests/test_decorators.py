# encoding: utf-8
# py27 compat

import pytest

from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Output,
    execute_pipeline,
    lambda_solid,
    solid,
)

from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.utility_solids import define_stub_solid

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument


def execute_isolated_solid(solid_def, environment_dict=None):
    return execute_pipeline(
        PipelineDefinition(name='test', solid_defs=[solid_def]), environment_dict=environment_dict
    )


def test_no_parens_solid():
    called = {}

    @lambda_solid
    def hello_world():
        called['yup'] = True

    result = execute_isolated_solid(hello_world)

    assert called['yup']


def test_empty_solid():
    called = {}

    @lambda_solid()
    def hello_world():
        called['yup'] = True

    result = execute_isolated_solid(hello_world)

    assert called['yup']


def test_solid():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].output_value()['foo'] == 'bar'


def test_solid_one_output():
    @lambda_solid
    def hello_world():
        return {'foo': 'bar'}

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].output_value()['foo'] == 'bar'


def test_solid_yield():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        yield Output(value={'foo': 'bar'})

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].output_value()['foo'] == 'bar'


def test_solid_result_return():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return Output(value={'foo': 'bar'})

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].output_value()['foo'] == 'bar'


def test_solid_with_explicit_empty_outputs():
    @solid(output_defs=[])
    def hello_world(_context):
        return 'foo'

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_isolated_solid(hello_world)

    assert (
        'Error in solid hello_world: Unexpectedly returned output foo of type '
        '<class \'str\'>. Solid is explicitly defined to return no results.'
    ) in str(exc_info.value) or (
        'Error in solid hello_world: Unexpectedly returned output foo of type '
        '<type \'str\'>. Solid is explicitly defined to return no results.'
    ) in str(
        exc_info.value
    )  # py2


def test_solid_with_implicit_single_output():
    @solid()
    def hello_world(_context):
        return 'foo'

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    solid_result = result.solid_result_list[0]
    assert solid_result.output_value() == 'foo'


def test_solid_return_list_instead_of_multiple_results():
    @solid(output_defs=[OutputDefinition(name='foo'), OutputDefinition(name='bar')])
    def hello_world(_context):
        return ['foo', 'bar']

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_isolated_solid(hello_world)

    assert 'unexpectedly returned output [\'foo\', \'bar\']' in str(exc_info.value)


def test_lambda_solid_with_name():
    @lambda_solid(name="foobar")
    def hello_world():
        return {'foo': 'bar'}

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].output_value()['foo'] == 'bar'


def test_solid_with_name():
    @solid(name="foobar", output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_isolated_solid(hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].output_value()['foo'] == 'bar'


def test_solid_with_input():
    @lambda_solid(input_defs=[InputDefinition(name="foo_to_foo")])
    def hello_world(foo_to_foo):
        return foo_to_foo

    pipeline = PipelineDefinition(
        solid_defs=[define_stub_solid('test_value', {'foo': 'bar'}), hello_world],
        dependencies={'hello_world': {'foo_to_foo': DependencyDefinition('test_value')}},
    )

    pipeline_result = execute_pipeline(pipeline)

    result = pipeline_result.result_for_solid('hello_world')

    assert result.success
    assert result.output_value()['foo'] == 'bar'


def test_lambda_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError, match='positional vararg'):

        @lambda_solid(input_defs=[InputDefinition(name="foo")])
        def vargs(foo, *args):
            pass


def test_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError, match='positional vararg'):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def vargs(context, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def wrong_name(context, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(
            input_defs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
            output_defs=[OutputDefinition()],
        )
        def wrong_name_2(context, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def no_context(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def extras(_context, foo, bar):
            pass

    @solid(
        input_defs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
        output_defs=[OutputDefinition()],
    )
    def valid_kwargs(context, **kwargs):
        pass

    @solid(
        input_defs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
        output_defs=[OutputDefinition()],
    )
    def valid(context, foo, bar):
        pass

    @solid
    def valid_because_inference(context, foo, bar):
        pass


def test_wrong_argument_to_pipeline():
    def non_solid_func():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match='You have passed a lambda or function non_solid_func'
    ):
        PipelineDefinition(solid_defs=[non_solid_func])

    with pytest.raises(
        DagsterInvalidDefinitionError, match='You have passed a lambda or function <lambda>'
    ):
        PipelineDefinition(solid_defs=[lambda x: x])


def test_descriptions():
    @solid(description='foo')
    def solid_desc(_context):
        pass

    assert solid_desc.description == 'foo'


def test_any_config_field():
    called = {}
    conf_value = 234

    @solid(config_field=Field(Any))
    def hello_world(context):
        assert context.solid_config == conf_value
        called['yup'] = True

    result = execute_isolated_solid(
        hello_world, environment_dict={'solids': {'hello_world': {'config': conf_value}}}
    )

    assert called['yup']


def test_solid_no_arg():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='does not have required positional parameter \'context\'.',
    ):

        @solid
        def noop():
            return
