from typing import Dict, Generator, Tuple

import pytest
from dagster import (
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    DagsterType,
    DagsterTypeCheckDidNotPass,
    In,
    Nothing,
    Out,
    Output,
    build_op_context,
    graph,
    op,
)
from dagster.core.execution.execute import execute_in_process


def execute_op_in_graph(an_op):
    @graph
    def my_graph():
        an_op()

    result = execute_in_process(my_graph)
    return result


def test_op():
    @op
    def my_op():
        pass

    execute_op_in_graph(my_op)


def test_ins():
    @op
    def upstream1():
        return 5

    @op
    def upstream2():
        return "6"

    @op(ins={"a": In(metadata={"x": 1}), "b": In(metadata={"y": 2})})
    def my_op(a: int, b: str) -> int:
        return a + int(b)

    @graph
    def my_graph():
        my_op(a=upstream1(), b=upstream2())

    result = execute_in_process(my_graph)
    assert result.success

    assert upstream1() == 5

    assert upstream2() == "6"

    assert my_op(1, "2") == 3


def test_out():
    @op(out=Out(metadata={"x": 1}))
    def my_op() -> int:
        return 1

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "result"
    assert my_op() == 1


def test_multi_out():
    @op(out={"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})})
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"

    assert my_op() == (1, "q")


def test_tuple_out():
    @op
    def my_op() -> Tuple[int, str]:
        return 1, "a"

    assert len(my_op.output_defs) == 1
    result = execute_op_in_graph(my_op)
    assert result.result_for_node("my_op").output_values == {"result": (1, "a")}

    assert my_op() == (1, "a")


def test_multi_out_yields():
    @op(out={"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})})
    def my_op():
        yield Output(output_name="a", value=1)
        yield Output(output_name="b", value=2)

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    result = execute_op_in_graph(my_op)
    assert result.result_for_node("my_op").output_values["a"] == 1
    assert result.result_for_node("my_op").output_values["b"] == 2

    assert [output.value for output in my_op()] == [1, 2]


def test_multi_out_optional():
    @op(out={"a": Out(metadata={"x": 1}, is_required=False), "b": Out(metadata={"y": 2})})
    def my_op():
        yield Output(output_name="b", value=2)

    result = execute_op_in_graph(my_op)
    assert result.result_for_node("my_op").output_values["b"] == 2

    assert [output.value for output in my_op()] == [2]


def test_ins_dict():
    @op
    def upstream1():
        return 5

    @op
    def upstream2():
        return "6"

    @op(
        ins={
            "a": In(metadata={"x": 1}),
            "b": In(metadata={"y": 2}),
        }
    )
    def my_op(a: int, b: str) -> int:
        return a + int(b)

    assert my_op.input_defs[0].dagster_type.typing_type == int
    assert my_op.input_defs[1].dagster_type.typing_type == str

    @graph
    def my_graph():
        my_op(a=upstream1(), b=upstream2())

    result = execute_in_process(my_graph)
    assert result.success

    assert my_op(a=1, b="2") == 3


def test_multi_out_dict():
    @op(out={"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})})
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[0].dagster_type.typing_type == int
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    assert my_op.output_defs[1].dagster_type.typing_type == str

    result = execute_op_in_graph(my_op)
    assert result.result_for_node("my_op").output_values["a"] == 1
    assert result.result_for_node("my_op").output_values["b"] == "q"

    assert my_op() == (1, "q")


def test_nothing_in():
    @op(out=Out(dagster_type=Nothing))
    def noop():
        pass

    @op(ins={"after": In(dagster_type=Nothing)})
    def on_complete():
        return "cool"

    @graph
    def nothing_test():
        on_complete(noop())

    result = execute_in_process(nothing_test)
    assert result.success


def test_op_config():
    @op(config_schema={"conf_str": str})
    def my_op(context):
        assert context.op_config == {"conf_str": "foo"}

    my_op(build_op_context(config={"conf_str": "foo"}))

    @graph
    def basic():
        my_op()

    result = execute_in_process(
        basic, run_config={"ops": {"basic": {"ops": {"my_op": {"config": {"conf_str": "foo"}}}}}}
    )
    assert result.success

    result = basic.to_job(
        config={"ops": {"my_op": {"config": {"conf_str": "foo"}}}}
    ).execute_in_process()
    assert result.success


even_type = DagsterType(
    name="EvenDagsterType",
    type_check_fn=lambda _, value: isinstance(value, int) and value % 2 == 0,
)
# Test typing override between out and annotation. Should they just match?
def test_out_dagster_type():
    @op(out=Out(dagster_type=even_type))
    def basic() -> int:
        return 6

    assert basic.output_defs[0].dagster_type == even_type
    assert basic() == 6


def test_multiout_dagster_type():
    @op(out={"a": Out(dagster_type=even_type), "b": Out(dagster_type=even_type)})
    def basic_multi() -> Tuple[int, int]:
        return 6, 6

    assert basic_multi() == (6, 6)


# Test creating a single, named op using the dictionary syntax. Document that annotation cannot be wrapped in a tuple for singleton case.
def test_multiout_single_entry():
    @op(out={"a": Out()})
    def single_output_op() -> int:
        return 5

    assert single_output_op() == 5
    result = execute_op_in_graph(single_output_op)
    assert result.result_for_node("single_output_op").output_values["a"] == 5


def test_tuple_named_single_output():
    # Ensure functionality in the case where you want to have a named tuple output
    @op(out={"a": Out()})
    def single_output_op_tuple() -> Tuple[int, int]:
        return (5, 5)

    assert single_output_op_tuple() == (5, 5)
    assert execute_op_in_graph(single_output_op_tuple).result_for_node(
        "single_output_op_tuple"
    ).output_values["a"] == (5, 5)


# Test creating a multi-out op with the incorrect annotation.
def test_op_multiout_incorrect_annotation():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Expected Tuple annotation for multiple outputs, but received non-tuple annotation.",
    ):

        @op(out={"a": Out(), "b": Out()})
        def _incorrect_annotation_op() -> int:
            pass


def test_op_typing_annotations():
    @op
    def my_dict_op() -> Dict[str, int]:
        return {"foo": 5}

    assert my_dict_op() == {"foo": 5}

    my_output = {"foo": 5}, ("foo",)

    @op(out={"a": Out(), "b": Out()})
    def my_dict_multiout() -> Tuple[Dict[str, int], Tuple[str]]:
        return {"foo": 5}, ("foo",)

    assert my_dict_multiout() == my_output
    result = execute_op_in_graph(my_dict_multiout)
    assert result.result_for_node("my_dict_multiout").output_values["a"] == my_output[0]
    assert result.result_for_node("my_dict_multiout").output_values["b"] == my_output[1]


# Test simplest possible multiout case
def test_op_multiout_base():
    @op(out={"a": Out(), "b": Out()})
    def basic_multiout() -> Tuple[int, str]:
        return (5, "foo")

    assert basic_multiout() == (5, "foo")
    result = execute_op_in_graph(basic_multiout)
    assert result.result_for_node("basic_multiout").output_values["a"] == 5
    assert result.result_for_node("basic_multiout").output_values["b"] == "foo"


# Test tuple size mismatch (larger and smaller)
def test_op_multiout_size_mismatch():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Expected Tuple annotation to have number of entries matching the number of outputs "
        "for more than one output. Expected 2 outputs but annotation has 3.",
    ):

        @op(out={"a": Out(), "b": Out()})
        def _basic_multiout_wrong_annotation() -> Tuple[int, int, int]:
            pass


# Document what happens when someone tries to use type annotations with Output
def test_type_annotations_with_output():
    @op
    def my_op_returns_output() -> Output:
        return Output(5)

    with pytest.raises(DagsterTypeCheckDidNotPass):
        my_op_returns_output()


# Document what happens when someone tries to use type annotations with generator
def test_type_annotations_with_generator():
    @op
    def my_op_yields_output() -> Generator[Output, None, None]:
        yield Output(5)

    assert list(my_op_yields_output())[0].value == 5
    result = execute_op_in_graph(my_op_yields_output)
    assert result.result_for_node("my_op_yields_output").output_values["result"] == 5


def test_op_config_entry_collision():
    @op(config_schema={"foo": str})
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()
        my_op.alias("my_op2")()

    my_job = my_graph.to_job()

    with pytest.raises(DagsterInvalidConfigError, match="Received both field"):
        my_job.execute_in_process(
            run_config={
                "solids": {"my_op": {"config": {"foo": "bar"}}},
                "ops": {"my_op2": {"config": {"foo": "bar"}}},
            }
        )

    @graph
    def nest_collision():
        my_graph()

    my_nested_graph_job = nest_collision.to_job()

    with pytest.raises(
        DagsterInvalidConfigError,
        match="Received both field 'solids' and field 'ops' in config. Please use one or the other.",
    ):
        my_nested_graph_job.execute_in_process(
            run_config={
                "ops": {
                    "my_graph": {
                        "solids": {"my_op": {"config": {"foo": "bar"}}},
                        "ops": {"my_op2": {"config": {"foo": "bar"}}},
                    }
                }
            }
        )
