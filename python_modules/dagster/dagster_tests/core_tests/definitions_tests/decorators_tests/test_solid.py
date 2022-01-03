import re

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
    composite_solid,
    execute_pipeline,
    execute_solid,
    graph,
    lambda_solid,
    op,
    pipeline,
    solid,
)
from dagster.core.errors import DagsterInvalidInvocationError
from dagster.core.utility_solids import define_stub_solid

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument, redefined-outer-name


def test_no_parens_solid():
    called = {}

    @lambda_solid
    def hello_world():
        called["yup"] = True

    result = execute_solid(hello_world)

    assert called["yup"]


def test_empty_solid():
    called = {}

    @lambda_solid()
    def hello_world():
        called["yup"] = True

    result = execute_solid(hello_world)

    assert called["yup"]


def test_solid():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_one_output():
    @lambda_solid
    def hello_world():
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_yield():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        yield Output(value={"foo": "bar"})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_result_return():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return Output(value={"foo": "bar"})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_with_explicit_empty_outputs():
    @solid(output_defs=[])
    def hello_world(_context):
        return "foo"

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_solid(hello_world)

    assert (
        'Error in solid "hello_world": Unexpectedly returned output foo of type '
        "<class 'str'>. Solid is explicitly defined to return no results."
    ) in str(exc_info.value)


def test_solid_with_implicit_single_output():
    @solid()
    def hello_world(_context):
        return "foo"

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value() == "foo"


def test_solid_return_list_instead_of_multiple_results():
    @solid(output_defs=[OutputDefinition(name="foo"), OutputDefinition(name="bar")])
    def hello_world(_context):
        return ["foo", "bar"]

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_solid(hello_world)

    assert "unexpectedly returned output ['foo', 'bar']" in str(exc_info.value)


def test_lambda_solid_with_name():
    @lambda_solid(name="foobar")
    def hello_world():
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_with_name():
    @solid(name="foobar", output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_with_input():
    @lambda_solid(input_defs=[InputDefinition(name="foo_to_foo")])
    def hello_world(foo_to_foo):
        return foo_to_foo

    the_pipeline = PipelineDefinition(
        solid_defs=[define_stub_solid("test_value", {"foo": "bar"}), hello_world],
        name="test",
        dependencies={"hello_world": {"foo_to_foo": DependencyDefinition("test_value")}},
    )

    pipeline_result = execute_pipeline(the_pipeline)

    result = pipeline_result.result_for_solid("hello_world")

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_lambda_solid_with_underscore_input():
    # Document that it is possible for lambda_solid to take an arg that the decorator machinery
    # would otherwise think is a context.
    @lambda_solid()
    def emit_input(_):
        return _

    @lambda_solid
    def emit_five():
        return 5

    @pipeline
    def basic_lambda_pipeline():
        emit_input(emit_five())

    pipeline_result = execute_pipeline(basic_lambda_pipeline)

    result = pipeline_result.result_for_solid("emit_input")

    assert result.success
    assert result.output_value() == 5


def test_lambda_solid_definition_errors():
    with pytest.raises(
        DagsterInvalidDefinitionError, match=re.escape("positional vararg parameter '*args'")
    ):

        @lambda_solid(input_defs=[InputDefinition(name="foo")])
        def vargs(foo, *args):
            pass


def test_solid_definition_errors():
    with pytest.raises(
        DagsterInvalidDefinitionError, match=re.escape("positional vararg parameter '*args'")
    ):

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
        DagsterInvalidDefinitionError, match="You have passed a lambda or function non_solid_func"
    ):
        PipelineDefinition(solid_defs=[non_solid_func], name="test")

    with pytest.raises(
        DagsterInvalidDefinitionError, match="You have passed a lambda or function <lambda>"
    ):
        PipelineDefinition(solid_defs=[lambda x: x], name="test")


def test_descriptions():
    @solid(description="foo")
    def solid_desc(_context):
        pass

    assert solid_desc.description == "foo"


def test_any_config_field():
    called = {}
    conf_value = 234

    @solid(config_schema=Field(Any))
    def hello_world(context):
        assert context.solid_config == conf_value
        called["yup"] = True

    result = execute_solid(
        hello_world, run_config={"solids": {"hello_world": {"config": conf_value}}}
    )

    assert called["yup"]


def test_solid_required_resources_no_arg():
    @solid(required_resource_keys={"foo"})
    def _noop():
        return


def test_solid_config_no_arg():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="'_noop2' decorated function requires positional parameter 'context',",
    ):

        @solid(config_schema={"foo": str})
        def _noop2():
            return


def test_solid_docstring():
    @solid
    def foo_solid(_):
        """FOO_DOCSTRING"""
        return

    @lambda_solid
    def bar_solid():
        """BAR_DOCSTRING"""
        return

    @solid(name="baz")
    def baz_solid(_):
        """BAZ_DOCSTRING"""
        return

    @lambda_solid(name="quux")
    def quux_solid():
        """QUUX_DOCSTRING"""
        return

    @composite_solid
    def comp_solid():
        """COMP_DOCSTRING"""
        foo_solid()

    @pipeline
    def the_pipeline():
        """THE_DOCSTRING"""
        quux_solid()

    @op
    def the_op():
        """OP_DOCSTRING"""

    @graph
    def the_graph():
        """GRAPH_DOCSTRING"""
        the_op()

    assert foo_solid.__doc__ == "FOO_DOCSTRING"
    assert foo_solid.description == "FOO_DOCSTRING"
    assert foo_solid.__name__ == "foo_solid"
    assert bar_solid.__doc__ == "BAR_DOCSTRING"
    assert bar_solid.description == "BAR_DOCSTRING"
    assert bar_solid.__name__ == "bar_solid"
    assert baz_solid.__doc__ == "BAZ_DOCSTRING"
    assert baz_solid.description == "BAZ_DOCSTRING"
    assert baz_solid.__name__ == "baz_solid"
    assert quux_solid.__doc__ == "QUUX_DOCSTRING"
    assert quux_solid.description == "QUUX_DOCSTRING"
    assert quux_solid.__name__ == "quux_solid"
    assert comp_solid.__doc__ == "COMP_DOCSTRING"
    assert comp_solid.description == "COMP_DOCSTRING"
    assert comp_solid.__name__ == "comp_solid"
    assert the_pipeline.__doc__ == "THE_DOCSTRING"
    assert the_pipeline.description == "THE_DOCSTRING"
    assert the_pipeline.__name__ == "the_pipeline"
    assert the_op.__doc__ == "OP_DOCSTRING"
    assert the_op.description == "OP_DOCSTRING"
    assert the_op.__name__ == "the_op"
    assert the_graph.__doc__ == "GRAPH_DOCSTRING"
    assert the_graph.description == "GRAPH_DOCSTRING"
    assert the_graph.__name__ == "the_graph"


def test_solid_yields_single_bare_value():
    @solid
    def return_iterator(_):
        yield 1

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for solid "return_iterator" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by solids must be wrapped in one of these types. If your solid has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your solid compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
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
        match=re.escape('Compute function for solid "return_iterator" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by solids must be wrapped in one of these types. If your solid has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your solid compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
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
        match=re.escape('Compute function for solid "return_iterator" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by solids must be wrapped in one of these types. If your solid has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your solid compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
        ),
    ):
        result = execute_solid(return_iterator)


def test_input_default():
    @lambda_solid
    def foo(bar="ok"):
        return bar

    result = execute_solid(foo)
    assert result.output_value() == "ok"


def test_solid_within_solid():
    @solid
    def basic():
        pass

    @solid
    def shouldnt_work():
        basic()

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Attempted to invoke @solid 'basic' within @solid 'shouldnt_work', which is undefined behavior. In order to compose invocations, check out the graph API",
    ):
        shouldnt_work()

    # Ensure that after exiting, proper usage isn't flagged
    basic()
