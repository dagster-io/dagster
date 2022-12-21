from dagster import OpDefinition, build_op_context
from docs_snippets.concepts.ops_jobs_graphs.ops import (
    context_op,
    my_configurable_op,
    my_input_op,
    my_multi_output_op,
    my_multiple_output_annotation_op,
    my_op,
    my_op_factory,
    my_output_op,
    my_single_tuple_output_op,
    my_typed_input_op,
    return_annotation_op,
)


def generate_stub_input_values(solid):
    input_values = {}

    default_values = {"String": "abc", "Int": 1, "Any": 1}

    input_defs = solid.input_defs
    for input_def in input_defs:
        input_values[input_def.name] = default_values.get(
            str(input_def.dagster_type.display_name), 2
        )

    return input_values


def test_ops_compile_and_execute():
    ops = [
        my_input_op,
        my_typed_input_op,
        my_output_op,
        my_multi_output_op,
        my_op,
    ]

    for op in ops:
        input_values = generate_stub_input_values(op)
        op(**input_values)


def test_context_op():
    context_op(build_op_context(config={"name": "my_name"}))


def test_my_configurable_op():
    my_configurable_op(
        build_op_context(config={"api_endpoint": "https://localhost:3000"})
    )


def test_op_factory():
    factory_op = my_op_factory("test")
    assert isinstance(factory_op, OpDefinition)


def test_return_annotation_op():
    assert return_annotation_op() == 5


def test_multiple_output_annotation_op():
    assert my_multiple_output_annotation_op() == (5, "foo")


def test_my_single_tuple_output_op():
    assert my_single_tuple_output_op() == (5, "foo")
