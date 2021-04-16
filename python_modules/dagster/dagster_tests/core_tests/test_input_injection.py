import pytest
from dagster import (
    DagsterInvalidConfigError,
    DependencyDefinition,
    InputDefinition,
    List,
    OutputDefinition,
    PipelineDefinition,
    SolidInvocation,
    String,
    execute_pipeline,
    solid,
)


def test_string_from_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("string_input", String)])
    def str_as_input(_context, string_input):
        assert string_input == "foo"
        called["yup"] = True

    pipeline = PipelineDefinition(
        name="test_string_from_inputs_pipeline", solid_defs=[str_as_input]
    )

    result = execute_pipeline(
        pipeline, {"solids": {"str_as_input": {"inputs": {"string_input": {"value": "foo"}}}}}
    )

    assert result.success
    assert called["yup"]


def test_string_from_aliased_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("string_input", String)])
    def str_as_input(_context, string_input):
        assert string_input == "foo"
        called["yup"] = True

    pipeline = PipelineDefinition(
        solid_defs=[str_as_input],
        name="test",
        dependencies={SolidInvocation("str_as_input", alias="aliased"): {}},
    )

    result = execute_pipeline(
        pipeline, {"solids": {"aliased": {"inputs": {"string_input": {"value": "foo"}}}}}
    )

    assert result.success
    assert called["yup"]


def test_string_missing_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("string_input", String)])
    def str_as_input(_context, string_input):  # pylint: disable=W0613
        called["yup"] = True

    pipeline = PipelineDefinition(name="missing_inputs", solid_defs=[str_as_input])
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(pipeline)

    assert len(exc_info.value.errors) == 1

    expected_suggested_config = {"solids": {"str_as_input": {"inputs": {"string_input": "..."}}}}
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "solids" at the root.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    assert "yup" not in called


def test_string_missing_input_collision():
    called = {}

    @solid(output_defs=[OutputDefinition(String)])
    def str_as_output(_context):
        return "bar"

    @solid(input_defs=[InputDefinition("string_input", String)])
    def str_as_input(_context, string_input):  # pylint: disable=W0613
        called["yup"] = True

    pipeline = PipelineDefinition(
        name="overlapping",
        solid_defs=[str_as_input, str_as_output],
        dependencies={"str_as_input": {"string_input": DependencyDefinition("str_as_output")}},
    )
    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(
            pipeline, {"solids": {"str_as_input": {"inputs": {"string_input": "bar"}}}}
        )

    assert (
        'Error 1: Received unexpected config entry "inputs" at path root:solids:str_as_input.'
        in str(exc_info.value)
    )

    assert "yup" not in called


def test_composite_input_type():
    called = {}

    @solid(input_defs=[InputDefinition("list_string_input", List[String])])
    def str_as_input(_context, list_string_input):
        assert list_string_input == ["foo"]
        called["yup"] = True

    pipeline = PipelineDefinition(
        name="test_string_from_inputs_pipeline", solid_defs=[str_as_input]
    )

    result = execute_pipeline(
        pipeline,
        {"solids": {"str_as_input": {"inputs": {"list_string_input": [{"value": "foo"}]}}}},
    )

    assert result.success
    assert called["yup"]
