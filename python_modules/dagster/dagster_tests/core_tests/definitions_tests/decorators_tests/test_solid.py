import re

import pytest

from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DependencyDefinition,
    Field,
    In,
    Out,
    Output,
    graph,
    op,
)
from dagster._core.utility_solids import define_stub_op
from dagster._legacy import (
    PipelineDefinition,
    composite_solid,
    execute_pipeline,
    execute_solid,
    pipeline,
)

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument, redefined-outer-name


def test_no_parens_op():
    called = {}

    @op
    def hello_world():
        called["yup"] = True

    result = execute_solid(hello_world)

    assert called["yup"]


def test_empty_op():
    called = {}

    @op()
    def hello_world():
        called["yup"] = True

    result = execute_solid(hello_world)

    assert called["yup"]


def test_op():
    @op(out=Out())
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_op_one_output():
    @op
    def hello_world():
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_op_yield():
    @op(out=Out())
    def hello_world(_context):
        yield Output(value={"foo": "bar"})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_op_result_return():
    @op(out=Out())
    def hello_world(_context):
        return Output(value={"foo": "bar"})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_op_with_explicit_empty_outputs():
    @op(out={})
    def hello_world(_context):
        return "foo"

    with pytest.raises(DagsterInvariantViolationError):
        execute_solid(hello_world)


def test_op_with_implicit_single_output():
    @op()
    def hello_world(_context):
        return "foo"

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value() == "foo"


def test_op_return_list_instead_of_multiple_results():
    @op(out={"foo": Out(), "bar": Out()})
    def hello_world(_context):
        return ["foo", "bar"]

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        execute_solid(hello_world)


def test_op_with_name():
    @op(name="foobar", out=Out())
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_op_with_input():
    @op(ins={"foo_to_foo": In()})
    def hello_world(foo_to_foo):
        return foo_to_foo

    the_pipeline = PipelineDefinition(
        solid_defs=[define_stub_op("test_value", {"foo": "bar"}), hello_world],
        name="test",
        dependencies={"hello_world": {"foo_to_foo": DependencyDefinition("test_value")}},
    )

    pipeline_result = execute_pipeline(the_pipeline)

    result = pipeline_result.result_for_solid("hello_world")

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_op_definition_errors():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("positional vararg parameter '*args'"),
    ):

        @op(ins={"foo": In()}, out=Out())
        def vargs(context, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(ins={"foo": In()}, out=Out())
        def wrong_name(context, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(
            ins={"foo": In(), "bar": In()},
            out=Out(),
        )
        def wrong_name_2(context, foo):
            pass

    @op(
        ins={"foo": In(), "bar": In()},
        out=Out(),
    )
    def valid_kwargs(context, **kwargs):
        pass

    @op(
        ins={"foo": In(), "bar": In()},
        out=Out(),
    )
    def valid(context, foo, bar):
        pass

    @op
    def valid_because_inference(context, foo, bar):
        pass


def test_wrong_argument_to_pipeline():
    def non_op_func():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="You have passed a lambda or function non_op_func",
    ):
        PipelineDefinition(solid_defs=[non_op_func], name="test")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="You have passed a lambda or function <lambda>",
    ):
        PipelineDefinition(solid_defs=[lambda x: x], name="test")


def test_descriptions():
    @op(description="foo")
    def op_desc(_context):
        pass

    assert op_desc.description == "foo"


def test_any_config_field():
    called = {}
    conf_value = 234

    @op(config_schema=Field(Any))
    def hello_world(context):
        assert context.op_config == conf_value
        called["yup"] = True

    result = execute_solid(hello_world, run_config={"ops": {"hello_world": {"config": conf_value}}})

    assert called["yup"]


def test_op_required_resources_no_arg():
    @op(required_resource_keys={"foo"})
    def _noop():
        return


def test_op_config_no_arg():
    @op(config_schema={"foo": str})
    def _noop2():
        return


def test_op_docstring():
    @op
    def foo_op(_):
        """FOO_DOCSTRING"""
        return

    @op
    def bar_op():
        """BAR_DOCSTRING"""
        return

    @op(name="baz")
    def baz_op(_):
        """BAZ_DOCSTRING"""
        return

    @op(name="quux")
    def quux_op():
        """QUUX_DOCSTRING"""
        return

    @composite_solid
    def comp_solid():
        """COMP_DOCSTRING"""
        foo_op()

    @pipeline
    def the_pipeline():
        """THE_DOCSTRING"""
        quux_op()

    @op
    def the_op():
        """OP_DOCSTRING"""

    @graph
    def the_graph():
        """GRAPH_DOCSTRING"""
        the_op()

    assert foo_op.__doc__ == "FOO_DOCSTRING"
    assert foo_op.description == "FOO_DOCSTRING"
    assert foo_op.__name__ == "foo_op"
    assert bar_op.__doc__ == "BAR_DOCSTRING"
    assert bar_op.description == "BAR_DOCSTRING"
    assert bar_op.__name__ == "bar_op"
    assert baz_op.__doc__ == "BAZ_DOCSTRING"
    assert baz_op.description == "BAZ_DOCSTRING"
    assert baz_op.__name__ == "baz_op"
    assert quux_op.__doc__ == "QUUX_DOCSTRING"
    assert quux_op.description == "QUUX_DOCSTRING"
    assert quux_op.__name__ == "quux_op"
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


def test_op_yields_single_bare_value():
    @op
    def return_iterator(_):
        yield 1

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for op "return_iterator" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by ops must be wrapped in one of these types. If your op has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your op compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
        ),
    ):
        result = execute_solid(return_iterator)


def test_op_yields_multiple_bare_values():
    @op
    def return_iterator(_):
        yield 1
        yield 2

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for op "return_iterator" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by ops must be wrapped in one of these types. If your op has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your op compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
        ),
    ):
        result = execute_solid(return_iterator)


def test_op_returns_iterator():
    def iterator():
        for i in range(3):
            yield i

    @op
    def return_iterator(_):
        return iterator()

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape('Compute function for op "return_iterator" yielded a value of type <')
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by ops must be wrapped in one of these types. If your op has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your op compute function. If you are already using "
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
    @op
    def foo(bar="ok"):
        return bar

    result = execute_solid(foo)
    assert result.output_value() == "ok"
