import pytest

from dagster import (
    DagsterTypeCheckError,
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

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_dict)


def test_basic_python_dictionary_input_wrong():
    @lambda_solid(input_defs=[InputDefinition('data', dict)], output_def=OutputDefinition(str))
    def input_dict(data):
        return data['key']

    with pytest.raises(DagsterTypeCheckError):
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
