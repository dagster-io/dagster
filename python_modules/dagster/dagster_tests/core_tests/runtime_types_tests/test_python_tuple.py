from typing import Tuple

import pytest

from dagster import DagsterTypeCheckDidNotPass, In, Out, op
from dagster._core.types.python_tuple import create_typed_tuple
from dagster._legacy import execute_solid


def test_vanilla_tuple_output():
    @op(out=Out(tuple))
    def emit_tuple():
        return (1, 2)

    assert execute_solid(emit_tuple).output_value() == (1, 2)


def test_vanilla_tuple_output_fail():
    @op(out=Out(tuple))
    def emit_tuple():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_tuple)


def test_vanilla_tuple_input():
    @op(ins={"tt": In(dagster_type=tuple)})
    def take_tuple(tt):
        return tt

    assert execute_solid(take_tuple, input_values={"tt": (2, 3)}).output_value() == (
        2,
        3,
    )


def test_vanilla_tuple_input_fail():
    @op(ins={"tt": In(dagster_type=tuple)})
    def take_tuple(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_tuple, input_values={"tt": "fkjdf"})


def test_open_typing_tuple_output():
    @op(out=Out(Tuple))
    def emit_tuple():
        return (1, 2)

    assert execute_solid(emit_tuple).output_value() == (1, 2)


def test_open_typing_tuple_output_fail():
    @op(out=Out(Tuple))
    def emit_tuple():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_tuple)


def test_open_typing_tuple_input():
    @op(ins={"tt": In(dagster_type=Tuple)})
    def take_tuple(tt):
        return tt

    assert execute_solid(take_tuple, input_values={"tt": (2, 3)}).output_value() == (
        2,
        3,
    )


def test_open_typing_tuple_input_fail():
    @op(ins={"tt": In(dagster_type=Tuple)})
    def take_tuple(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_tuple, input_values={"tt": "fkjdf"})


def test_typed_python_tuple_directly():
    int_str_tuple = create_typed_tuple(int, str)

    int_str_tuple.type_check(None, (1, "foo"))

    res = int_str_tuple.type_check(None, None)
    assert not res.success

    res = int_str_tuple.type_check(None, "bar")
    assert not res.success

    res = int_str_tuple.type_check(None, (1, 2, 3))
    assert not res.success

    res = int_str_tuple.type_check(None, ("1", 2))
    assert not res.success


def test_nested_python_tuple_directly():
    int_str_tuple_kls = create_typed_tuple(int, str)

    nested_tuple = create_typed_tuple(bool, list, int_str_tuple_kls)

    nested_tuple.type_check(None, (True, [1], (1, "foo")))

    res = nested_tuple.type_check(None, None)
    assert not res.success

    res = nested_tuple.type_check(None, "bar")
    assert not res.success

    res = nested_tuple.type_check(None, (True, [1], (1, 2)))
    assert not res.success


def test_closed_typing_tuple_output():
    @op(out=Out(Tuple[int, int]))
    def emit_tuple():
        return (1, 2)

    assert execute_solid(emit_tuple).output_value() == (1, 2)


def test_closed_typing_tuple_output_fail():
    @op(out=Out(Tuple[int, int]))
    def emit_tuple():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_tuple)


def test_closed_typing_tuple_output_fail_wrong_member_types():
    @op(out=Out(Tuple[int, int]))
    def emit_tuple():
        return (1, "nope")

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_tuple)


def test_closed_typing_tuple_output_fail_wrong_length():
    @op(out=Out(Tuple[int, int]))
    def emit_tuple():
        return (1,)

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_tuple)


def test_closed_typing_tuple_input():
    @op(ins={"tt": In(dagster_type=Tuple[int, int])})
    def take_tuple(tt):
        return tt

    assert execute_solid(take_tuple, input_values={"tt": (2, 3)}).output_value() == (
        2,
        3,
    )


def test_closed_typing_tuple_input_fail():
    @op(ins={"tt": In(dagster_type=Tuple[int, int])})
    def take_tuple(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_tuple, input_values={"tt": "fkjdf"})
