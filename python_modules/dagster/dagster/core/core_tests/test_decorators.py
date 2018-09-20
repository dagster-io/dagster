import pytest
from dagster import (
    ConfigDefinition,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    ExecutionContext,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    Result,
    check,
    config,
    execute_pipeline,
    lambda_solid,
    solid,
)

from dagster.core.test_utils import execute_single_solid
from dagster.core.utility_solids import define_stub_solid

# This file tests a lot of parameter name stuff
# So these warnings are spurious
# unused variables, unused arguments
# pylint: disable=W0612, W0613


def create_test_context():
    return ExecutionContext()


def create_empty_test_env():
    return config.Environment()


def test_multiple_single_result():
    mr = MultipleResults(Result('value', 'output_one'))
    assert mr.results == [Result('value', 'output_one')]


def test_multiple_double_result():
    mr = MultipleResults(Result('value_one', 'output_one'), Result('value_two', 'output_two'))
    assert mr.results == [Result('value_one', 'output_one'), Result('value_two', 'output_two')]


def test_multiple_dict():
    mr = MultipleResults.from_dict({'output_one': 'value_one', 'output_two': 'value_two'})
    assert set(mr.results) == set(
        [Result('value_one', 'output_one'),
         Result('value_two', 'output_two')]
    )


def test_no_parens_solid():
    called = {}

    @lambda_solid
    def hello_world():
        called['yup'] = True

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert called['yup']


def test_empty_solid():
    called = {}

    @lambda_solid()
    def hello_world():
        called['yup'] = True

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert called['yup']


def test_solid():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_info):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_one_output():
    @lambda_solid
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_yield():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_info):
        yield Result(value={'foo': 'bar'})

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_result_return():
    @solid(outputs=[OutputDefinition()])
    def hello_world(_info):
        return Result(value={'foo': 'bar'})

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_multiple_outputs():
    @solid(outputs=[OutputDefinition(name="left"), OutputDefinition(name="right")])
    def hello_world(_info):
        return MultipleResults(
            Result(value={'foo': 'left'}, output_name='left'),
            Result(value={'foo': 'right'}, output_name='right')
        )

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    solid_result = result.result_list[0]
    assert solid_result.transformed_value('left')['foo'] == 'left'
    assert solid_result.transformed_value('right')['foo'] == 'right'


def test_dict_multiple_outputs():
    @solid(outputs=[OutputDefinition(name="left"), OutputDefinition(name="right")])
    def hello_world(_info):
        return MultipleResults.from_dict({
            'left': {
                'foo': 'left'
            },
            'right': {
                'foo': 'right'
            },
        })

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    solid_result = result.result_list[0]
    assert solid_result.transformed_value('left')['foo'] == 'left'
    assert solid_result.transformed_value('right')['foo'] == 'right'


def test_lambda_solid_with_name():
    @lambda_solid(name="foobar")
    def hello_world():
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_with_name():
    @solid(name="foobar", outputs=[OutputDefinition()])
    def hello_world(_info):
        return {'foo': 'bar'}

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_empty_test_env(),
    )

    assert result.success
    assert len(result.result_list) == 1
    assert result.result_list[0].transformed_value()['foo'] == 'bar'


def test_solid_with_input():
    @lambda_solid(inputs=[InputDefinition(name="foo_to_foo")])
    def hello_world(foo_to_foo):
        return foo_to_foo

    pipeline = PipelineDefinition(
        solids=[define_stub_solid('test_value', {'foo': 'bar'}), hello_world],
        dependencies={'hello_world': {
            'foo_to_foo': DependencyDefinition('test_value'),
        }}
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
        def vargs(info, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def wrong_name(info, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(
            inputs=[
                InputDefinition(name="foo"),
                InputDefinition(name="bar"),
            ],
            outputs=[OutputDefinition()]
        )
        def wrong_name_2(info, foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def no_info(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(inputs=[InputDefinition(name="foo")], outputs=[OutputDefinition()])
        def extras(_info, foo, bar):
            pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        outputs=[OutputDefinition()]
    )
    def valid_kwargs(info, **kwargs):
        pass

    @solid(
        inputs=[InputDefinition(name="foo"),
                InputDefinition(name="bar")],
        outputs=[OutputDefinition()]
    )
    def valid(info, foo, bar):
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


def test_any_config_definition():
    called = {}
    conf_value = 234

    @solid(config_def=ConfigDefinition())
    def hello_world(info):
        assert info.config == conf_value
        called['yup'] = True

    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=config.Environment(solids={'hello_world': config.Solid(conf_value)})
    )

    assert called['yup']
