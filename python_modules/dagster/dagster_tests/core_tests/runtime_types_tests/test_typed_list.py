# ruff: noqa: UP006
import typing

import dagster as dg
import pytest
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_basic_list_output_pass():
    @dg.op(out=dg.Out(list))
    def emit_list():
        return [1]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [1]


def test_basic_list_output_fail():
    @dg.op(out=dg.Out(list))
    def emit_list():
        return "foo"

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_basic_list_input_pass():
    @dg.op(ins={"alist": dg.In(list)})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [2]}
    ).output_value() == [2]


def test_basic_list_input_fail():
    @dg.op(ins={"alist": dg.In(list)})
    def ingest_list(alist):
        return alist

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": "foobar"})


def test_typing_list_output_pass():
    @dg.op(out=dg.Out(typing.List))
    def emit_list():
        return [1]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [1]


def test_typing_list_output_fail():
    @dg.op(out=dg.Out(typing.List))
    def emit_list():
        return "foo"

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_typing_list_input_pass():
    @dg.op(ins={"alist": dg.In(typing.List)})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [2]}
    ).output_value() == [2]


def test_typing_list_input_fail():
    @dg.op(ins={"alist": dg.In(typing.List)})
    def ingest_list(alist):
        return alist

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": "foobar"})


def test_typing_list_of_int_output_pass():
    @dg.op(out=dg.Out(typing.List[int]))
    def emit_list():
        return [1]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [1]


def test_typing_list_of_int_output_fail():
    @dg.op(out=dg.Out(typing.List[int]))
    def emit_list():
        return ["foo"]

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_typing_list_of_int_input_pass():
    @dg.op(ins={"alist": dg.In(typing.List[int])})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [2]}
    ).output_value() == [2]


def test_typing_list_of_int_input_fail():
    @dg.op(ins={"alist": dg.In(typing.List[int])})
    def ingest_list(alist):
        return alist

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": ["foobar"]})


LIST_LIST_INT = typing.List[typing.List[int]]


def test_typing_list_of_list_of_int_output_pass():
    @dg.op(out=dg.Out(LIST_LIST_INT))
    def emit_list():
        return [[1, 2], [3, 4]]

    assert wrap_op_in_graph_and_execute(emit_list).output_value() == [[1, 2], [3, 4]]


def test_typing_list_of_list_of_int_output_fail():
    @dg.op(out=dg.Out(LIST_LIST_INT))
    def emit_list():
        return [[1, 2], [3, "4"]]

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_list).output_value()


def test_typing_list_of_list_of_int_input_pass():
    @dg.op(ins={"alist": dg.In(LIST_LIST_INT)})
    def ingest_list(alist):
        return alist

    assert wrap_op_in_graph_and_execute(
        ingest_list, input_values={"alist": [[1, 2], [3, 4]]}
    ).output_value() == [
        [1, 2],
        [3, 4],
    ]


def test_typing_list_of_list_of_int_input_fail():
    @dg.op(ins={"alist": dg.In(LIST_LIST_INT)})
    def ingest_list(alist):
        return alist

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(ingest_list, input_values={"alist": [[1, 2], [3, "4"]]})
