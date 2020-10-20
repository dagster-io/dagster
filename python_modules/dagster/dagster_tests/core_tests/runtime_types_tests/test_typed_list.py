import typing

import pytest
from dagster import (
    DagsterTypeCheckDidNotPass,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)


def test_basic_list_output_pass():
    @lambda_solid(output_def=OutputDefinition(list))
    def emit_list():
        return [1]

    assert execute_solid(emit_list).output_value() == [1]


def test_basic_list_output_fail():
    @lambda_solid(output_def=OutputDefinition(list))
    def emit_list():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_list).output_value()


def test_basic_list_input_pass():
    @lambda_solid(input_defs=[InputDefinition("alist", list)])
    def ingest_list(alist):
        return alist

    assert execute_solid(ingest_list, input_values={"alist": [2]}).output_value() == [2]


def test_basic_list_input_fail():
    @lambda_solid(input_defs=[InputDefinition("alist", list)])
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(ingest_list, input_values={"alist": "foobar"})


def test_typing_list_output_pass():
    @lambda_solid(output_def=OutputDefinition(typing.List))
    def emit_list():
        return [1]

    assert execute_solid(emit_list).output_value() == [1]


def test_typing_list_output_fail():
    @lambda_solid(output_def=OutputDefinition(typing.List))
    def emit_list():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_list).output_value()


def test_typing_list_input_pass():
    @lambda_solid(input_defs=[InputDefinition("alist", typing.List)])
    def ingest_list(alist):
        return alist

    assert execute_solid(ingest_list, input_values={"alist": [2]}).output_value() == [2]


def test_typing_list_input_fail():
    @lambda_solid(input_defs=[InputDefinition("alist", typing.List)])
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(ingest_list, input_values={"alist": "foobar"})


def test_typing_list_of_int_output_pass():
    @lambda_solid(output_def=OutputDefinition(typing.List[int]))
    def emit_list():
        return [1]

    assert execute_solid(emit_list).output_value() == [1]


def test_typing_list_of_int_output_fail():
    @lambda_solid(output_def=OutputDefinition(typing.List[int]))
    def emit_list():
        return ["foo"]

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_list).output_value()


def test_typing_list_of_int_input_pass():
    @lambda_solid(input_defs=[InputDefinition("alist", typing.List[int])])
    def ingest_list(alist):
        return alist

    assert execute_solid(ingest_list, input_values={"alist": [2]}).output_value() == [2]


def test_typing_list_of_int_input_fail():
    @lambda_solid(input_defs=[InputDefinition("alist", typing.List[int])])
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(ingest_list, input_values={"alist": ["foobar"]})


LIST_LIST_INT = typing.List[typing.List[int]]


def test_typing_list_of_list_of_int_output_pass():
    @lambda_solid(output_def=OutputDefinition(LIST_LIST_INT))
    def emit_list():
        return [[1, 2], [3, 4]]

    assert execute_solid(emit_list).output_value() == [[1, 2], [3, 4]]


def test_typing_list_of_list_of_int_output_fail():
    @lambda_solid(output_def=OutputDefinition(LIST_LIST_INT))
    def emit_list():
        return [[1, 2], [3, "4"]]

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_list).output_value()


def test_typing_list_of_list_of_int_input_pass():
    @lambda_solid(input_defs=[InputDefinition("alist", LIST_LIST_INT)])
    def ingest_list(alist):
        return alist

    assert execute_solid(ingest_list, input_values={"alist": [[1, 2], [3, 4]]}).output_value() == [
        [1, 2],
        [3, 4],
    ]


def test_typing_list_of_list_of_int_input_fail():
    @lambda_solid(input_defs=[InputDefinition("alist", LIST_LIST_INT)])
    def ingest_list(alist):
        return alist

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(ingest_list, input_values={"alist": [[1, 2], [3, "4"]]})
