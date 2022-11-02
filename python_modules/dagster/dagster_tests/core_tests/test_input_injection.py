import pytest

from dagster import (
    DagsterInvalidConfigError,
    DependencyDefinition,
    GraphDefinition,
    In,
    List,
    NodeInvocation,
    Out,
    String,
    op,
)


def test_string_from_inputs():
    called = {}

    @op(ins={"string_input": In(String)})
    def str_as_input(_context, string_input):
        assert string_input == "foo"
        called["yup"] = True

    pipeline = GraphDefinition(
        name="test_string_from_inputs_pipeline", node_defs=[str_as_input]
    ).to_job()

    result = pipeline.execute_in_process(
        {"solids": {"str_as_input": {"inputs": {"string_input": {"value": "foo"}}}}},
    )

    assert result.success
    assert called["yup"]


def test_string_from_aliased_inputs():
    called = {}

    @op(ins={"string_input": In(String)})
    def str_as_input(_context, string_input):
        assert string_input == "foo"
        called["yup"] = True

    pipeline = GraphDefinition(
        node_defs=[str_as_input],
        name="test",
        dependencies={NodeInvocation("str_as_input", alias="aliased"): {}},
    ).to_job()

    result = pipeline.execute_in_process(
        {"solids": {"aliased": {"inputs": {"string_input": {"value": "foo"}}}}},
    )

    assert result.success
    assert called["yup"]


def test_string_missing_inputs():
    called = {}

    @op(ins={"string_input": In(String)})
    def str_as_input(_context, string_input):  # pylint: disable=W0613
        called["yup"] = True

    pipeline = GraphDefinition(name="missing_inputs", node_defs=[str_as_input]).to_job()
    with pytest.raises(
        DagsterInvalidConfigError, match='Missing required config entry "ops"'
    ) as exc_info:
        pipeline.execute_in_process()

    assert len(exc_info.value.errors) == 1

    expected_suggested_config = {"ops": {"str_as_input": {"inputs": {"string_input": "..."}}}}

    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    assert "yup" not in called


def test_string_missing_input_collision():
    called = {}

    @op(out=Out(String))
    def str_as_output(_context):
        return "bar"

    @op(ins={"string_input": In(String)})
    def str_as_input(_context, string_input):  # pylint: disable=W0613
        called["yup"] = True

    pipeline = GraphDefinition(
        name="overlapping",
        node_defs=[str_as_input, str_as_output],
        dependencies={"str_as_input": {"string_input": DependencyDefinition("str_as_output")}},
    ).to_job()
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        pipeline.execute_in_process({"ops": {"str_as_input": {"inputs": {"string_input": "bar"}}}})

    assert (
        'Error 1: Received unexpected config entry "inputs" at path root:ops:str_as_input.'
        in str(exc_info.value)
    )

    assert "yup" not in called


def test_composite_input_type():
    called = {}

    @op(ins={"list_string_input": In(List[String])})
    def str_as_input(_context, list_string_input):
        assert list_string_input == ["foo"]
        called["yup"] = True

    pipeline = GraphDefinition(
        name="test_string_from_inputs_pipeline", node_defs=[str_as_input]
    ).to_job()

    result = pipeline.execute_in_process(
        {"solids": {"str_as_input": {"inputs": {"list_string_input": [{"value": "foo"}]}}}},
    )

    assert result.success
    assert called["yup"]
