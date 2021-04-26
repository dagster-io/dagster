import re

import pytest
from dagster import (
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidDefinition,
    solid,
)
from dagster.core.utility_solids import define_stub_solid


def solid_a_b_list():
    return [
        SolidDefinition(
            name="A",
            input_defs=[],
            output_defs=[OutputDefinition()],
            compute_fn=lambda _context, _inputs: None,
        ),
        SolidDefinition(
            name="B",
            input_defs=[InputDefinition("b_input")],
            output_defs=[],
            compute_fn=lambda _context, _inputs: None,
        ),
    ]


def test_create_pipeline_with_bad_solids_list():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='"solids" arg to "a_pipeline" is not a list. Got',
    ):
        PipelineDefinition(
            name="a_pipeline", solid_defs=define_stub_solid("stub", [{"a key": "a value"}])
        )


def test_circular_dep():
    with pytest.raises(DagsterInvalidDefinitionError, match="circular reference"):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            name="test",
            dependencies={"A": {}, "B": {"b_input": DependencyDefinition("B")}},
        )


def test_from_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='solid "NOTTHERE" in dependency dictionary not found'
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            name="test",
            dependencies={
                "A": {},
                "B": {"b_input": DependencyDefinition("A")},
                "NOTTHERE": {"b_input": DependencyDefinition("A")},
            },
        )


def test_from_non_existant_input():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='solid "B" does not have input "not_an_input"'
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"not_an_input": DependencyDefinition("A")}},
        )


def test_to_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='solid "NOTTHERE" not found in solid list'
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            name="test",
            dependencies={"A": {}, "B": {"b_input": DependencyDefinition("NOTTHERE")}},
        )


def test_to_solid_output_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='solid "A" does not have output "NOTTHERE"'
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"b_input": DependencyDefinition("A", output="NOTTHERE")}},
        )


def test_invalid_item_in_solid_list():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Invalid item in solid list: 'not_a_solid'"
    ):
        PipelineDefinition(
            solid_defs=["not_a_solid"],
            name="test",
        )


def test_one_layer_off_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Received a IDependencyDefinition one layer too high under key B",
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(), name="test", dependencies={"B": DependencyDefinition("A")}
        )


def test_malformed_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Expected IDependencyDefinition for solid "B" input "b_input"',
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"b_input": {"b_input": DependencyDefinition("A")}}},
        )


def test_list_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='The expected type for "dependencies" is Dict'
    ):
        PipelineDefinition(solid_defs=solid_a_b_list(), name="test", dependencies=[])


def test_pass_unrelated_type_to_field_error_solid_definition():

    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config_schema="nope")
        def _a_solid(_context):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: 'nope'. 'nope' cannot be resolved."
    )


def test_pass_unrelated_type_to_field_error_resource_definition():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:
        ResourceDefinition(resource_fn=lambda _: None, config_schema="wut")

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: 'wut'. 'wut' cannot be resolved."
    )


def test_pass_unrelated_type_in_nested_field_error_resource_definition():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:
        ResourceDefinition(
            resource_fn=lambda _: None, config_schema={"field": {"nested_field": "wut"}}
        )
    assert str(exc_info.value).startswith("Error")

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'field': {'nested_field': 'wut'}}. "
        "Error at stack path :field:nested_field. 'wut' cannot be resolved."
    )


def test_pass_incorrect_thing_to_field():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        Field("nope")

    assert str(exc_info.value) == (
        "Attempted to pass 'nope' to a Field that expects a valid dagster type "
        "usable in config (e.g. Dict, Int, String et al)."
    )


def test_bad_output_definition():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got foo."
        ),
    ):
        _output = OutputDefinition("foo")

    # Test the case where the object is not hashable
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got {'foo': 'bar'}, which isn't hashable. "
            "Did you pass an instance of a type instead of the type?"
        ),
    ):
        _output = OutputDefinition({"foo": "bar"})

    # Test the case where the object throws in __nonzero__, e.g. pandas.DataFrame
    class Exotic:
        def __nonzero__(self):
            raise ValueError("Love too break the core Python APIs in widely-used libraries")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got <dagster_tests.core_tests.definitions_tests.test_definition_errors"
        )
        + "("  # py27
        + re.escape(".test_bad_output_definition.<locals>")
        + ")?"
        + re.escape(".Exotic object"),
    ):
        _output = OutputDefinition(Exotic())


def test_solid_tags():
    @solid(tags={"good": {"ok": "fine"}})
    def _fine_tags(_):
        pass

    class X:
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Could not JSON encode value",
    ):

        @solid(tags={"bad": X()})
        def _bad_tags(_):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r'JSON encoding "\[1, 2\]" of value "\(1, 2\)" is not equivalent to original value',
    ):

        @solid(tags={"set_comes_back_as_dict": (1, 2)})
        def _also_bad_tags(_):
            pass
