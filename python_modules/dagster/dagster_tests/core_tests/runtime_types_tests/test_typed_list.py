# ruff: noqa: UP006

import typing

import pytest
from dagster import DagsterTypeCheckDidNotPass, In, Out, op
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_basic_list_output_pass():
    @op(out=Out(list))
    def emit_list():
        return [1]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [1]


def test_basic_list_output_fail():
    @op(out=Out(list))
    def emit_list():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_basic_list_input_pass():
    @op(ins={"alist": In(list)})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [2]}
    ).output_value() == [2]


def test_basic_list_input_fail():
    @op(ins={"alist": In(list)})
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": "foobar"})


def test_typing_list_output_pass():
    @op(out=Out(typing.List))
    def emit_list():
        return [1]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [1]


def test_typing_list_output_fail():
    @op(out=Out(typing.List))
    def emit_list():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_typing_list_input_pass():
    @op(ins={"alist": In(typing.List)})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [2]}
    ).output_value() == [2]


def test_typing_list_input_fail():
    @op(ins={"alist": In(typing.List)})
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": "foobar"})


def test_typing_list_of_int_output_pass():
    @op(out=Out(typing.List[int]))
    def emit_list():
        return [1]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [1]


def test_typing_list_of_int_output_fail():
    @op(out=Out(typing.List[int]))
    def emit_list():
        return ["foo"]

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_typing_list_of_int_input_pass():
    @op(ins={"alist": In(typing.List[int])})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [2]}
    ).output_value() == [2]


def test_typing_list_of_int_input_fail():
    @op(ins={"alist": In(typing.List[int])})
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": ["foobar"]})


LIST_LIST_INT = typing.List[typing.List[int]]


def test_typing_list_of_list_of_int_output_pass():
    @op(out=Out(LIST_LIST_INT))
    def emit_list():
        return [[1, 2], [3, 4]]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [[1, 2], [3, 4]]


def test_typing_list_of_list_of_int_output_fail():
    @op(out=Out(LIST_LIST_INT))
    def emit_list():
        return [[1, 2], [3, "4"]]

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_typing_list_of_list_of_int_input_pass():
    @op(ins={"alist": In(LIST_LIST_INT)})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [[1, 2], [3, 4]]}
    ).output_value() == [
        [1, 2],
        [3, 4],
    ]


def test_typing_list_of_list_of_int_input_fail():
    @op(ins={"alist": In(LIST_LIST_INT)})
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": [[1, 2], [3, "4"]]})
