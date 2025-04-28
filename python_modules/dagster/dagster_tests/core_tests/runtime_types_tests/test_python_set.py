# ruff: noqa: UP006

import typing

import pytest
from dagster import DagsterTypeCheckDidNotPass, In, Optional, Out, op
from dagster._core.types.dagster_type import resolve_dagster_type
from dagster._core.types.python_set import create_typed_runtime_set
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_vanilla_set_output():
    @op(out=Out(set))
    def emit_set():
        return {1, 2}

    assert wrap_op_in_graph_and_execute(emit_set).output_value() == {1, 2}


def test_vanilla_set_output_fail():
    @op(out=Out(set))
    def emit_set():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_set)


def test_vanilla_set_input():
    @op(ins={"tt": In(dagster_type=set)})
    def take_set(tt):
        return tt

    assert wrap_op_in_graph_and_execute(take_set, input_values={"tt": {2, 3}}).output_value() == {
        2,
        3,
    }


def test_vanilla_set_input_fail():
    @op(ins={"tt": In(dagster_type=set)})
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(take_set, input_values={"tt": "fkjdf"})


def test_open_typing_set_output():
    @op(out=Out(typing.Set))
    def emit_set():
        return {1, 2}

    assert wrap_op_in_graph_and_execute(emit_set).output_value() == {1, 2}


def test_open_typing_set_output_fail():
    @op(out=Out(typing.Set))
    def emit_set():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_set)


def test_open_typing_set_input():
    @op(ins={"tt": In(dagster_type=typing.Set)})
    def take_set(tt):
        return tt

    assert wrap_op_in_graph_and_execute(take_set, input_values={"tt": {2, 3}}).output_value() == {
        2,
        3,
    }


def test_open_typing_set_input_fail():
    @op(ins={"tt": In(dagster_type=typing.Set)})
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(take_set, input_values={"tt": "fkjdf"})


def test_runtime_set_of_int():
    set_dagster_type = create_typed_runtime_set(int)

    set_dagster_type.type_check(None, {1})  # pyright: ignore[reportArgumentType]
    set_dagster_type.type_check(None, set())  # pyright: ignore[reportArgumentType]

    res = set_dagster_type.type_check(None, None)  # pyright: ignore[reportArgumentType]
    assert not res.success

    res = set_dagster_type.type_check(None, "nope")  # pyright: ignore[reportArgumentType]
    assert not res.success

    res = set_dagster_type.type_check(None, {"nope"})  # pyright: ignore[reportArgumentType]
    assert not res.success


def test_runtime_optional_set():
    set_dagster_type = resolve_dagster_type(Optional[create_typed_runtime_set(int)])

    set_dagster_type.type_check(None, {1})  # pyright: ignore[reportArgumentType]
    set_dagster_type.type_check(None, set())  # pyright: ignore[reportArgumentType]
    set_dagster_type.type_check(None, None)  # pyright: ignore[reportArgumentType]

    res = set_dagster_type.type_check(None, "nope")  # pyright: ignore[reportArgumentType]
    assert not res.success

    res = set_dagster_type.type_check(None, {"nope"})  # pyright: ignore[reportArgumentType]
    assert not res.success


def test_closed_typing_set_input():
    @op(ins={"tt": In(dagster_type=typing.Set[int])})
    def take_set(tt):
        return tt

    assert wrap_op_in_graph_and_execute(take_set, input_values={"tt": {2, 3}}).output_value() == {
        2,
        3,
    }


def test_closed_typing_set_input_fail():
    @op(ins={"tt": In(dagster_type=typing.Set[int])})
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(take_set, input_values={"tt": "fkjdf"})

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(take_set, input_values={"tt": {"fkjdf"}})


def test_typed_set_type_loader():
    @op(ins={"tt": In(dagster_type=typing.Set[int])})
    def take_set(tt):
        return tt

    expected_output = set([1, 2, 3, 4])
    assert (
        wrap_op_in_graph_and_execute(
            take_set,
            run_config={"ops": {"take_set": {"inputs": {"tt": list(expected_output)}}}},
            do_input_mapping=False,
        ).output_value()
        == expected_output
    )
