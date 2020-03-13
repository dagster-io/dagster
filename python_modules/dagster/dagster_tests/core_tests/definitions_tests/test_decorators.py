# encoding: utf-8
# py27 compat

import re
from datetime import datetime

import pytest

from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DependencyDefinition,
    Field,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    ScheduleDefinition,
    execute_pipeline,
    execute_solid,
    lambda_solid,
    pipeline,
    schedules,
    solid,
)
from dagster.core.definitions.decorators import (
    daily_schedule,
    hourly_schedule,
    monthly_schedule,
    weekly_schedule,
)
from dagster.core.utility_solids import define_stub_solid

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument, redefined-outer-name


def test_no_parens_solid():
    called = {}

    @lambda_solid
    def hello_world():
        called['yup'] = True

    result = execute_solid(hello_world)

    assert called['yup']


def test_empty_solid():
    called = {}

    @lambda_solid()
    def hello_world():
        called['yup'] = True

    result = execute_solid(hello_world)

    assert called['yup']


def test_solid():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()['foo'] == 'bar'


def test_solid_one_output():
    @lambda_solid
    def hello_world():
        return {'foo': 'bar'}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()['foo'] == 'bar'


def test_solid_yield():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        yield Output(value={'foo': 'bar'})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()['foo'] == 'bar'


def test_solid_result_return():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return Output(value={'foo': 'bar'})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()['foo'] == 'bar'


def test_solid_with_explicit_empty_outputs():
    @solid(output_defs=[])
    def hello_world(_context):
        return 'foo'

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_solid(hello_world)

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

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value() == 'foo'


def test_solid_return_list_instead_of_multiple_results():
    @solid(output_defs=[OutputDefinition(name='foo'), OutputDefinition(name='bar')])
    def hello_world(_context):
        return ['foo', 'bar']

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_solid(hello_world)

    assert 'unexpectedly returned output [\'foo\', \'bar\']' in str(exc_info.value)


def test_lambda_solid_with_name():
    @lambda_solid(name="foobar")
    def hello_world():
        return {'foo': 'bar'}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()['foo'] == 'bar'


def test_solid_with_name():
    @solid(name="foobar", output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {'foo': 'bar'}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()['foo'] == 'bar'


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

    @solid(config=Field(Any))
    def hello_world(context):
        assert context.solid_config == conf_value
        called['yup'] = True

    result = execute_solid(
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


def test_scheduler():
    @schedules
    def define_scheduler():
        return [
            ScheduleDefinition(
                name="my_schedule",
                cron_schedule="* * * * *",
                pipeline_name="test_pipeline",
                environment_dict={},
            )
        ]


def test_schedule_decorators_sanity():
    @solid
    def do_nothing(_):
        pass

    @pipeline
    def foo_pipeline():
        do_nothing()

    @monthly_schedule(
        pipeline_name='foo_pipeline',
        execution_day_of_month=3,
        start_date=datetime(year=2019, month=1, day=1),
    )
    def monthly_foo_schedule():
        return {}

    @weekly_schedule(
        pipeline_name='foo_pipeline',
        execution_day_of_week=1,
        start_date=datetime(year=2019, month=1, day=1),
    )
    def weekly_foo_schedule():
        return {}

    @daily_schedule(
        pipeline_name='foo_pipeline', start_date=datetime(year=2019, month=1, day=1),
    )
    def daily_foo_schedule():
        return {}

    @hourly_schedule(
        pipeline_name='foo_pipeline', start_date=datetime(year=2019, month=1, day=1),
    )
    def hourly_foo_schedule():
        return {}


def test_schedule_decorators_bad():
    @solid
    def do_nothing(_):
        pass

    @pipeline
    def foo_pipeline():
        do_nothing()

    with pytest.raises(DagsterInvalidDefinitionError):

        @monthly_schedule(
            pipeline_name='foo_pipeline',
            execution_day_of_month=32,
            start_date=datetime(year=2019, month=1, day=1),
        )
        def monthly_foo_schedule_over():
            return {}

    with pytest.raises(DagsterInvalidDefinitionError):

        @monthly_schedule(
            pipeline_name='foo_pipeline',
            execution_day_of_month=0,
            start_date=datetime(year=2019, month=1, day=1),
        )
        def monthly_foo_schedule_under():
            return {}

    with pytest.raises(DagsterInvalidDefinitionError):

        @weekly_schedule(
            pipeline_name='foo_pipeline',
            execution_day_of_week=7,
            start_date=datetime(year=2019, month=1, day=1),
        )
        def weekly_foo_schedule_over():
            return {}


def test_solid_docstring():
    @solid
    def foo_solid(_):
        '''FOO_DOCSTRING'''
        return

    @lambda_solid
    def bar_solid():
        '''BAR_DOCSTRING'''
        return

    @solid(name='baz')
    def baz_solid(_):
        '''BAZ_DOCSTRING'''
        return

    @lambda_solid(name='quux')
    def quux_solid():
        '''QUUX_DOCSTRING'''
        return

    assert foo_solid.__doc__ == 'FOO_DOCSTRING'
    assert bar_solid.__doc__ == 'BAR_DOCSTRING'
    assert baz_solid.__doc__ == 'BAZ_DOCSTRING'
    assert quux_solid.__doc__ == 'QUUX_DOCSTRING'


def test_solid_yields_single_bare_value():
    @solid
    def return_iterator(_):
        yield 1

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for solid return_iterator yielded a value of type <')
        + r'(class|type)'
        + re.escape(
            ' \'int\'> rather than an instance of Output, Materialization, or ExpectationResult. '
            'Values yielded by solids must be wrapped in one of these types. If your solid has a '
            'single output and yields no other events, you may want to use `return` instead of '
            '`yield` in the body of your solid compute function. If you are already using '
            '`return`, and you expected to return a value of type <'
        )
        + r'(class|type)'
        + re.escape(
            ' \'int\'>, you may be inadvertently returning a generator rather than the value you '
            'expected.'
        ),
    ):
        result = execute_solid(return_iterator)


def test_solid_yields_multiple_bare_values():
    @solid
    def return_iterator(_):
        yield 1
        yield 2

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for solid return_iterator yielded a value of type <')
        + r'(class|type)'
        + re.escape(
            ' \'int\'> rather than an instance of Output, Materialization, or ExpectationResult. '
            'Values yielded by solids must be wrapped in one of these types. If your solid has a '
            'single output and yields no other events, you may want to use `return` instead of '
            '`yield` in the body of your solid compute function. If you are already using '
            '`return`, and you expected to return a value of type <'
        )
        + r'(class|type)'
        + re.escape(
            ' \'int\'>, you may be inadvertently returning a generator rather than the value you '
            'expected.'
        ),
    ):
        result = execute_solid(return_iterator)


def test_solid_returns_iterator():
    def iterator():
        for i in range(3):
            yield i

    @solid
    def return_iterator(_):
        return iterator()

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for solid return_iterator yielded a value of type <')
        + r'(class|type)'
        + re.escape(
            ' \'int\'> rather than an instance of Output, Materialization, or ExpectationResult. '
            'Values yielded by solids must be wrapped in one of these types. If your solid has a '
            'single output and yields no other events, you may want to use `return` instead of '
            '`yield` in the body of your solid compute function. If you are already using '
            '`return`, and you expected to return a value of type <'
        )
        + r'(class|type)'
        + re.escape(
            ' \'int\'>, you may be inadvertently returning a generator rather than the value you '
            'expected.'
        ),
    ):
        result = execute_solid(return_iterator)
