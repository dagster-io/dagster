import re
import typing

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    DagsterTypeCheckDidNotPass,
    Dict,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
    usable_as_dagster_type,
)


def test_basic_python_dictionary_output():
    @lambda_solid(output_def=OutputDefinition(dict))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}


def test_basic_python_dictionary_input():
    @lambda_solid(input_defs=[InputDefinition("data", dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_python_dictionary_wrong():
    @lambda_solid(output_def=OutputDefinition(dict))
    def emit_dict():
        return 1

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_python_dictionary_input_wrong():
    @lambda_solid(input_defs=[InputDefinition("data", dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data["key"]

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(input_dict, input_values={"data": 123})


def test_execute_dict_from_config():
    @lambda_solid(input_defs=[InputDefinition("data", dict)], output_def=OutputDefinition(str))
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
    @lambda_solid(output_def=OutputDefinition(dict))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}


def test_basic_dagster_dictionary_input():
    @lambda_solid(input_defs=[InputDefinition("data", Dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_typing_dictionary_output():
    @lambda_solid(output_def=OutputDefinition(typing.Dict))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}


def test_basic_typing_dictionary_input():
    @lambda_solid(
        input_defs=[InputDefinition("data", typing.Dict)], output_def=OutputDefinition(str)
    )
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_closed_typing_dictionary_wrong():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[int, int]))
    def emit_dict():
        return 1

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_closed_typing_dictionary_output():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, str]))
    def emit_dict():
        return {"key": "value"}

    assert execute_solid(emit_dict).output_value() == {"key": "value"}
    assert emit_dict.output_defs[0].dagster_type.key == "TypedPythonDict.String.String"
    assert emit_dict.output_defs[0].dagster_type.key_type.unique_name == "String"
    assert emit_dict.output_defs[0].dagster_type.value_type.unique_name == "String"


def test_basic_closed_typing_dictionary_input():
    @lambda_solid(
        input_defs=[InputDefinition("data", typing.Dict[str, str])],
        output_def=OutputDefinition(str),
    )
    def input_dict(data):
        return data["key"]

    assert (
        execute_solid(input_dict, input_values={"data": {"key": "value"}}).output_value() == "value"
    )


def test_basic_closed_typing_dictionary_key_wrong():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, str]))
    def emit_dict():
        return {1: "foo"}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_closed_typing_dictionary_value_wrong():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, str]))
    def emit_dict():
        return {"foo": 1}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_complicated_dictionary_typing_pass():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {"foo": [{1: 1, 2: 2}]}

    assert execute_solid(emit_dict).output_value() == {"foo": [{1: 1, 2: 2}]}


def test_complicated_dictionary_typing_fail():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {"foo": [{1: 1, "2": 2}]}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_dict_type_loader():
    test_input = {"hello": 5, "goodbye": 42}

    @lambda_solid(input_defs=[InputDefinition("dict_input", dagster_type=typing.Dict[str, int])])
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

    @lambda_solid(
        input_defs=[InputDefinition("dict_input", dagster_type=typing.Dict[str, CustomType])]
    )
    def emit_dict(dict_input):
        return dict_input

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.compile(
            'Input "dict_input" in solid '
            '"emit_dict" is not connected to the output of a previous solid and can not be loaded '
            "from configuration, creating an impossible to execute pipeline. Possible solutions are:"
        ),
    ):
        execute_solid(
            emit_dict,
            run_config={"solids": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
        )


def test_dict_type_loader_inner_type_mismatch():

    test_input = {"hello": "foo", "goodbye": "bar"}

    @lambda_solid(input_defs=[InputDefinition("dict_input", dagster_type=typing.Dict[str, int])])
    def emit_dict(dict_input):
        return dict_input

    # TODO: change this depending on the resolution of
    # https://github.com/dagster-io/dagster/issues/3180
    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(
            emit_dict,
            run_config={"solids": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
        )
