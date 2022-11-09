import typing

import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DagsterTypeCheckDidNotPass,
    Dict,
    In,
    Out,
    op,
    usable_as_dagster_type,
)
from dagster._legacy import execute_solid


def test_basic_python_dictionary_output():
    @op(out=Out(dict))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}


def test_basic_python_dictionary_input():
    @op(ins={"data": In(dict)}, out=Out(str))
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_python_dictionary_wrong():
    @op(out=Out(dict))
    def emit_dict():
        return 1

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_python_dictionary_input_wrong():
    @op(ins={"data": In(dict)}, out=Out(str))
    def input_dict(data):
        return data["key"]

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(input_dict, input_values={"data": 123})


def test_execute_dict_from_config():
    @op(ins={"data": In(dict)}, out=Out(str))
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(
            input_dict,
            run_config={"solids": {"input_dict": {"inputs": {"data": {"key": "in_config"}}}}},
        ).output_value()
        == "in_config"
    )


def test_dagster_dictionary_output():
    @op(out=Out(dict))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}


def test_basic_dagster_dictionary_input():
    @op(ins={"data": In(Dict)}, out=Out(str))
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_typing_dictionary_output():
    @op(out=Out(typing.Dict))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}


def test_basic_typing_dictionary_input():
    @op(
        ins={"data": In(typing.Dict)},
        out=Out(str),
    )
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_closed_typing_dictionary_wrong():
    @op(out=Out(typing.Dict[int, int]))
    def emit_dict():
        return 1

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_closed_typing_dictionary_output():
    @op(out=Out(typing.Dict[str, str]))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}
    assert emit_dict.output_defs[0].dagster_type.key == "TypedPythonDict.String.String"
    assert emit_dict.output_defs[0].dagster_type.key_type.unique_name == "String"
    assert emit_dict.output_defs[0].dagster_type.value_type.unique_name == "String"


def test_basic_closed_typing_dictionary_input():
    @op(
        ins={"data": In(typing.Dict[str, str])},
        out=Out(str),
    )
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_closed_typing_dictionary_key_wrong():
    @op(out=Out(typing.Dict[str, str]))
    def emit_dict():
        return {1: "foo"}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_closed_typing_dictionary_value_wrong():
    @op(out=Out(typing.Dict[str, str]))
    def emit_dict():
        return {"foo": 1}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_complicated_dictionary_typing_pass():
    @op(out=Out(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {"foo": [{1: 1, 2: 2}]}

    assert execute_solid(emit_dict).output_value() == {"foo": [{1: 1, 2: 2}]}


def test_complicated_dictionary_typing_fail():
    @op(out=Out(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {"foo": [{1: 1, "2": 2}]}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_dict_type_loader():
    test_input = {"hello": 5, "goodbye": 42}

    @op(ins={"dict_input": In(dagster_type=typing.Dict[str, int])})
    def emit_dict(dict_input):
        return dict_input

    result = execute_solid(
        emit_dict,
        run_config={"solids": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
    )
    assert result.success
    assert result.output_value() == test_input


def test_dict_type_loader_typing_fail():
    @usable_as_dagster_type
    class CustomType(str):
        pass

    test_input = {"hello": "foo", "goodbye": "bar"}

    @op(ins={"dict_input": In(dagster_type=typing.Dict[str, CustomType])})
    def emit_dict(dict_input):
        return dict_input

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Input 'dict_input' of op 'emit_dict' has no way of being resolved.",
    ):
        execute_solid(
            emit_dict,
            run_config={"op": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
        )


def test_dict_type_loader_inner_type_mismatch():

    test_input = {"hello": "foo", "goodbye": "bar"}

    @op(ins={"dict_input": In(dagster_type=typing.Dict[str, int])})
    def emit_dict(dict_input):
        return dict_input

    # TODO: change this depending on the resolution of
    # https://github.com/dagster-io/dagster/issues/3180
    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(
            emit_dict,
            run_config={"ops": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
        )
