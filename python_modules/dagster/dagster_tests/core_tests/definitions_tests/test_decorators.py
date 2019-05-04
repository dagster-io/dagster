# encoding: utf-8
# py27 compat

import pytest

from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    ExecutionContext,
    Field,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    Result,
    execute_pipeline,
    lambda_solid,
    solid,
)

from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.test_utils import execute_single_solid_in_isolation
from dagster.core.utility_solids import define_stub_solid

# This file tests a lot of parameter name stuff
# So these warnings are spurious
# unused variables, unused arguments
# pylint: disable=W0612, W0613


def create_test_context():
    return ExecutionContext()


def test_multiple_single_result():
    mr = MultipleResults(Result('value', 'output_one'))
    assert mr.results == [Result('value', 'output_one')]


def test_multiple_double_result():
    mr = MultipleResults(Result('value_one', 'output_one'), Result('value_two', 'output_two'))
    assert mr.results == [Result('value_one', 'output_one'), Result('value_two', 'output_two')]


def test_multiple_dict():
    mr = MultipleResults.from_dict({'output_one': 'value_one', 'output_two': 'value_two'})
    assert set(mr.results) == set(
        [Result('value_one', 'output_one'), Result('value_two', 'output_two')]
    )


def test_no_parens_solid():
    called = {}

    @lambda_solid
    def hello_world():
        called['yup'] = True

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert called['yup']


def test_empty_solid():
    called = {}

    @lambda_solid()
    def hello_world():
        called['yup'] = True

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert called['yup']


def test_solid():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_one_output():
    @lambda_solid
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_yield():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_context):
        yield Result(value={'foo': 'bar'})

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_result_return():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_context):
        return Result(value={'foo': 'bar'})

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_multiple_outputs():
    @solid(outputs=[OutputDefinition(name="left"), OutputDefinition(name="right")])
    def hello_world(_context):
        return MultipleResults(
            Result(value={'foo': 'left'}, output_name='left'),
            Result(value={'foo': 'right'}, output_name='right'),
        )

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    solid_result = result.solid_result_list[0]
    assert solid_result.transformed_value('left')['foo'] == 'left'
    assert solid_result.transformed_value('right')['foo'] == 'right'


def test_dict_multiple_outputs():
    @solid(outputs=[OutputDefinition(name="left"), OutputDefinition(name="right")])
    def hello_world(_context):
        return MultipleResults.from_dict({'left': {'foo': 'left'}, 'right': {'foo': 'right'}})

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    solid_result = result.solid_result_list[0]
    assert solid_result.transformed_value('left')['foo'] == 'left'
    assert solid_result.transformed_value('right')['foo'] == 'right'


def test_solid_with_explicit_empty_outputs():
    @solid(outputs=[])
    def hello_world(_context):
        return 'foo'

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_single_solid_in_isolation(create_test_context(), hello_world)

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

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    solid_result = result.solid_result_list[0]
    assert solid_result.transformed_value() == 'foo'


def test_solid_return_list_instead_of_multiple_results():
    @solid(outputs=[OutputDefinition(name='foo'), OutputDefinition(name='bar')])
    def hello_world(_context):
        return ['foo', 'bar']

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert 'unexpectedly returned output [\'foo\', \'bar\']' in str(exc_info.value)


def test_lambda_solid_with_name():
    @lambda_solid(name="foobar")
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_with_name():
    @solid(name="foobar", outputs=[OutputDefinition()])
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_single_solid_in_isolation(create_test_context(), hello_world)

    assert result.success
    assert len(result.solid_result_list) == 1
    assert result.solid_result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_with_input():
    @lambda_solid(inputs=[InputDefinition(name="foo_to_foo")])
    def hello_world(foo_to_foo):
        return foo_to_foo

    pipeline = PipelineDefinition(
        solids=[define_stub_solid('test_value', {'foo': 'bar'}), hello_world],
        dependencies={'hello_world': {'foo_to_foo': DependencyDefinition('test_value')}},
    )

    pipeline_result = execute_pipeline(pipeline)

    result = pipeline_result.result_for_solid('hello_world')

    assert result.success
    assert result.transformed_value()['foo'] == 'bar'


def test_lambda_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError, match='positional vararg'):

        @lambda_solid(inputs=[InputDefinition(name="foo")])
        def vargs(foo, *args):
            pass


def test_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError, match='positional vararg'):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def vargs(context, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def wrong_name(context, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(
            inputs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
            outputs=[OutputDefinition()],
        )
        def wrong_name_2(context, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def no_context(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def extras(_context, foo, bar):
            pass

    @solid(
        inputs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
        outputs=[OutputDefinition()],
    )
    def valid_kwargs(context, **kwargs):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
        outputs=[OutputDefinition()],
    )
    def valid(context, foo, bar):
        pass


def test_wrong_argument_to_pipeline():
    def non_solid_func():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match='You have passed a lambda or function non_solid_func'
    ):
        PipelineDefinition(solids=[non_solid_func])

    with pytest.raises(
        DagsterInvalidDefinitionError, match='You have passed a lambda or function <lambda>'
    ):
        PipelineDefinition(solids=[lambda x: x])


def test_descriptions():
    @solid(description='foo')
    def solid_desc():
        pass

    assert solid_desc.description == 'foo'


def test_any_config_field():
    called = {}
    conf_value = 234

    @solid(config_field=Field(Any))
    def hello_world(context):
        assert context.solid_config == conf_value
        called['yup'] = True

    result = execute_single_solid_in_isolation(
        create_test_context(),
        hello_world,
        environment={'solids': {'hello_world': {'config': conf_value}}},
    )

    assert called['yup']
