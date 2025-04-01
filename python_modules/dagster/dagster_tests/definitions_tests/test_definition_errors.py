import re

import pytest
from dagster import (
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Field,
    GraphDefinition,
    In,
    OpDefinition,
    Out,
    ResourceDefinition,
    op,
)
from dagster._check import ParameterCheckError
from dagster._core.utility_ops import create_stub_op


def solid_a_b_list():
    return [
        OpDefinition(
            name="A",
            ins={},
            outs={"result": Out()},
            compute_fn=lambda _context, _inputs: None,
        ),
        OpDefinition(
            name="B",
            ins={"b_input": In()},
            outs={},
            compute_fn=lambda _context, _inputs: None,
        ),
    ]


def test_create_job_with_bad_ops_list():
    with pytest.raises(ParameterCheckError, match=r'Param "node_defs" is not a Sequence'):
        GraphDefinition(name="a_pipeline", node_defs=create_stub_op("stub", [{"a key": "a value"}]))  # pyright: ignore[reportArgumentType]


def test_circular_dep():
    with pytest.raises(DagsterInvalidDefinitionError, match="circular reference"):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"A": {}, "B": {"b_input": DependencyDefinition("B")}},
        )


def test_from_op_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='node "NOTTHERE" in dependency dictionary not found',
    ):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={
                "A": {},
                "B": {"b_input": DependencyDefinition("A")},
                "NOTTHERE": {"b_input": DependencyDefinition("A")},
            },
        )


def test_from_non_existant_input():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='op "B" does not have input "not_an_input"',
    ):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"not_an_input": DependencyDefinition("A")}},
        )


def test_to_op_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='node "NOTTHERE" not found in node list'
    ):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"A": {}, "B": {"b_input": DependencyDefinition("NOTTHERE")}},
        )


def test_to_op_output_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='node "A" does not have output "NOTTHERE"'
    ):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"b_input": DependencyDefinition("A", output="NOTTHERE")}},
        )


def test_invalid_item_in_op_list():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Invalid item in node list: 'not_a_op'"
    ):
        GraphDefinition(
            node_defs=["not_a_op"],  # pyright: ignore[reportArgumentType]
            name="test",
        )


def test_one_layer_off_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Received a IDependencyDefinition one layer too high under key B",
    ):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": DependencyDefinition("A")},  # pyright: ignore[reportArgumentType]
        )


def test_malformed_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Expected IDependencyDefinition for node "B" input "b_input"',
    ):
        GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"b_input": {"b_input": DependencyDefinition("A")}}},  # pyright: ignore[reportArgumentType]
        )


def test_list_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r'The expected type for "dependencies" is Union\[Mapping\[',
    ):
        GraphDefinition(node_defs=solid_a_b_list(), name="test", dependencies=[])  # pyright: ignore[reportArgumentType]


def test_pass_unrelated_type_to_field_error_op_definition():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @op(config_schema="nope")
        def _a_op(_context):
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

    assert (
        str(exc_info.value)
        == "Attempted to pass 'nope' to a Field that expects a valid dagster type "
        "usable in config (e.g. Dict, Int, String et al)."
    )


def test_bad_out():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got foo."
        ),
    ):
        _output = Out("foo")  # pyright: ignore[reportArgumentType]

    # Test the case where the object is not hashable
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got {'foo': 'bar'}, which isn't hashable. "
            "Did you pass an instance of a type instead of the type?"
        ),
    ):
        _output = Out({"foo": "bar"})  # pyright: ignore[reportArgumentType]

    # Test the case where the object throws in __nonzero__, e.g. pandas.DataFrame
    class Exotic:
        def __nonzero__(self):
            raise ValueError("Love too break the core Python APIs in widely-used libraries")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Invalid type: dagster_type must be an instance of DagsterType or a Python type",
    ):
        _output = Out(Exotic())  # pyright: ignore[reportArgumentType]


def test_op_tags():
    @op(tags={"good": {"ok": "fine"}})
    def _fine_tags(_):
        pass

    class X:
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Could not JSON encode value",
    ):

        @op(tags={"bad": X()})
        def _bad_tags(_):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r'JSON encoding "\[1, 2\]" of value "\(1, 2\)" is not equivalent to original value',
    ):

        @op(tags={"set_comes_back_as_dict": (1, 2)})
        def _also_bad_tags(_):
            pass
