import typing

import pytest

from dagster import (
    DagsterTypeCheckDidNotPass,
    Dict,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)


def test_basic_python_dictionary_output():
    @lambda_solid(output_def=OutputDefinition(dict))
    def emit_dict():
        return {'key': 'value'}

    assert execute_solid(emit_dict).output_value() == {'key': 'value'}


def test_basic_python_dictionary_input():
    @lambda_solid(input_defs=[InputDefinition('data', dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data['key']

    assert (
        execute_solid(input_dict, input_values={'data': {'key': 'value'}}).output_value() == 'value'
    )


def test_basic_python_dictionary_wrong():
    @lambda_solid(output_def=OutputDefinition(dict))
    def emit_dict():
        return 1

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_python_dictionary_input_wrong():
    @lambda_solid(input_defs=[InputDefinition('data', dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data['key']

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(input_dict, input_values={'data': 123})


def test_execute_dict_from_config():
    @lambda_solid(input_defs=[InputDefinition('data', dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data['key']

    assert (
        execute_solid(
            input_dict,
            environment_dict={'solids': {'input_dict': {'inputs': {'data': {'key': 'in_config'}}}}},
        ).output_value()
        == 'in_config'
    )


def test_dagster_dictionary_output():
    @lambda_solid(output_def=OutputDefinition(dict))
    def emit_dict():
        return {'key': 'value'}

    assert execute_solid(emit_dict).output_value() == {'key': 'value'}


def test_basic_dagster_dictionary_input():
    @lambda_solid(input_defs=[InputDefinition('data', Dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data['key']

    assert (
        execute_solid(input_dict, input_values={'data': {'key': 'value'}}).output_value() == 'value'
    )


def test_basic_typing_dictionary_output():
    @lambda_solid(output_def=OutputDefinition(typing.Dict))
    def emit_dict():
        return {'key': 'value'}

    assert execute_solid(emit_dict).output_value() == {'key': 'value'}


def test_basic_typing_dictionary_input():
    @lambda_solid(
        input_defs=[InputDefinition('data', typing.Dict)], output_def=OutputDefinition(str)
    )
    def input_dict(data):
        return data['key']

    assert (
        execute_solid(input_dict, input_values={'data': {'key': 'value'}}).output_value() == 'value'
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
        return {'key': 'value'}

    assert execute_solid(emit_dict).output_value() == {'key': 'value'}
    assert emit_dict.output_defs[0].runtime_type.key == 'TypedPythonDict.String.String'
    assert emit_dict.output_defs[0].runtime_type.key_type.name == 'String'
    assert emit_dict.output_defs[0].runtime_type.value_type.name == 'String'


def test_basic_closed_typing_dictionary_input():
    @lambda_solid(
        input_defs=[InputDefinition('data', typing.Dict[str, str])],
        output_def=OutputDefinition(str),
    )
    def input_dict(data):
        return data['key']

    assert (
        execute_solid(input_dict, input_values={'data': {'key': 'value'}}).output_value() == 'value'
    )


def test_basic_closed_typing_dictionary_key_wrong():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, str]))
    def emit_dict():
        return {1: 'foo'}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_basic_closed_typing_dictionary_value_wrong():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, str]))
    def emit_dict():
        return {'foo': 1}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)


def test_complicated_dictionary_typing_pass():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {'foo': [{1: 1, 2: 2}]}

    assert execute_solid(emit_dict).output_value() == {'foo': [{1: 1, 2: 2}]}


def test_complicated_dictionary_typing_fail():
    @lambda_solid(output_def=OutputDefinition(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {'foo': [{1: 1, '2': 2}]}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict)
