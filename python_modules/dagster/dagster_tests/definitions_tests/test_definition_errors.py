import re

import dagster as dg
import pytest
from dagster._check import ParameterCheckError
from dagster._core.utility_ops import create_stub_op


def solid_a_b_list():
    return [
        dg.OpDefinition(
            name="A",
            ins={},
            outs={"result": dg.Out()},
            compute_fn=lambda _context, _inputs: None,
        ),
        dg.OpDefinition(
            name="B",
            ins={"b_input": dg.In()},
            outs={},
            compute_fn=lambda _context, _inputs: None,
        ),
    ]


def test_create_job_with_bad_ops_list():
    with pytest.raises(ParameterCheckError, match=r'Param "node_defs" is not a Sequence'):
        dg.GraphDefinition(
            name="a_pipeline",
            node_defs=create_stub_op("stub", [{"a key": "a value"}]),  # pyright: ignore[reportArgumentType]
        )


def test_circular_dep():
    with pytest.raises(dg.DagsterInvalidDefinitionError, match="circular reference"):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"A": {}, "B": {"b_input": dg.DependencyDefinition("B")}},
        )


def test_from_op_not_there():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match='node "NOTTHERE" in dependency dictionary not found',
    ):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={
                "A": {},
                "B": {"b_input": dg.DependencyDefinition("A")},
                "NOTTHERE": {"b_input": dg.DependencyDefinition("A")},
            },
        )


def test_from_non_existant_input():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match='op "B" does not have input "not_an_input"',
    ):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"not_an_input": dg.DependencyDefinition("A")}},
        )


def test_to_op_not_there():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match='node "NOTTHERE" not found in node list'
    ):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"A": {}, "B": {"b_input": dg.DependencyDefinition("NOTTHERE")}},
        )


def test_to_op_output_not_there():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match='node "A" does not have output "NOTTHERE"'
    ):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"b_input": dg.DependencyDefinition("A", output="NOTTHERE")}},
        )


def test_invalid_item_in_op_list():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="Invalid item in node list: 'not_a_op'"
    ):
        dg.GraphDefinition(
            node_defs=["not_a_op"],  # pyright: ignore[reportArgumentType]
            name="test",
        )


def test_one_layer_off_dependencies():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Received a IDependencyDefinition one layer too high under key B",
    ):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": dg.DependencyDefinition("A")},  # pyright: ignore[reportArgumentType]
        )


def test_malformed_dependencies():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match='Expected IDependencyDefinition for node "B" input "b_input"',
    ):
        dg.GraphDefinition(
            node_defs=solid_a_b_list(),
            name="test",
            dependencies={"B": {"b_input": {"b_input": dg.DependencyDefinition("A")}}},  # pyright: ignore[reportArgumentType]
        )


def test_list_dependencies():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r'The expected type for "dependencies" is Union\[Mapping\[',
    ):
        dg.GraphDefinition(node_defs=solid_a_b_list(), name="test", dependencies=[])  # pyright: ignore[reportArgumentType]


def test_pass_unrelated_type_to_field_error_op_definition():
    with pytest.raises(dg.DagsterInvalidConfigDefinitionError) as exc_info:

        @dg.op(config_schema="nope")
        def _a_op(_context):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: 'nope'. 'nope' cannot be resolved."
    )


def test_pass_unrelated_type_to_field_error_resource_definition():
    with pytest.raises(dg.DagsterInvalidConfigDefinitionError) as exc_info:
        dg.ResourceDefinition(resource_fn=lambda _: None, config_schema="wut")

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: 'wut'. 'wut' cannot be resolved."
    )


def test_pass_unrelated_type_in_nested_field_error_resource_definition():
    with pytest.raises(dg.DagsterInvalidConfigDefinitionError) as exc_info:
        dg.ResourceDefinition(
            resource_fn=lambda _: None, config_schema={"field": {"nested_field": "wut"}}
        )
    assert str(exc_info.value).startswith("Error")

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'field': {'nested_field': 'wut'}}. "
        "Error at stack path :field:nested_field. 'wut' cannot be resolved."
    )


def test_pass_incorrect_thing_to_field():
    with pytest.raises(dg.DagsterInvalidDefinitionError) as exc_info:
        dg.Field("nope")

    assert (
        str(exc_info.value)
        == "Attempted to pass 'nope' to a Field that expects a valid dagster type "
        "usable in config (e.g. Dict, Int, String et al)."
    )


def test_bad_out():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got foo."
        ),
    ):
        _output = dg.Out("foo")  # pyright: ignore[reportArgumentType]

    # Test the case where the object is not hashable
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
            "got {'foo': 'bar'}, which isn't hashable. "
            "Did you pass an instance of a type instead of the type?"
        ),
    ):
        _output = dg.Out({"foo": "bar"})  # pyright: ignore[reportArgumentType]

    # Test the case where the object throws in __nonzero__, e.g. pandas.DataFrame
    class Exotic:
        def __nonzero__(self):
            raise ValueError("Love too break the core Python APIs in widely-used libraries")

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Invalid type: dagster_type must be an instance of DagsterType or a Python type",
    ):
        _output = dg.Out(Exotic())  # pyright: ignore[reportArgumentType]


def test_op_tags():
    @dg.op(tags={"good": {"ok": "fine"}})
    def _fine_tags(_):
        pass

    class X:
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Could not JSON encode value",
    ):

        @dg.op(tags={"bad": X()})
        def _bad_tags(_):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r'JSON encoding "\[1, 2\]" of value "\(1, 2\)" is not equivalent to original value',
    ):

        @dg.op(tags={"set_comes_back_as_dict": (1, 2)})
        def _also_bad_tags(_):
            pass
