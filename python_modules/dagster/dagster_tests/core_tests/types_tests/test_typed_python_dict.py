import pytest

from dagster import (
    DagsterTypeCheckError,
    Dict,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)


def test_typed_python_dict():
    int_to_int = Dict[int, int].inst()

    int_to_int.type_check({1: 1})


def test_typed_python_dict_failure():
    int_to_int = Dict[int, int].inst()

    res = int_to_int.type_check({1: '1'})
    assert not res.success


def test_basic_solid_dict_int_int_output():
    @lambda_solid(output_def=OutputDefinition(Dict[int, int]))
    def emit_dict_int_int():
        return {1: 1}

    assert execute_solid(emit_dict_int_int).output_value() == {1: 1}


def test_basic_solid_dict_int_int_output_faile():
    @lambda_solid(output_def=OutputDefinition(Dict[int, int]))
    def emit_dict_int_int():
        return {1: '1'}

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_dict_int_int)


def test_basic_solid_dict_int_int_input_pass():
    @lambda_solid(input_defs=[InputDefinition('ddict', Dict[int, int])])
    def emit_dict_int_int(ddict):
        return ddict

    assert execute_solid(emit_dict_int_int, input_values={'ddict': {1: 2}}).output_value() == {1: 2}


def test_basic_solid_dict_int_int_input_fails():
    @lambda_solid(input_defs=[InputDefinition('ddict', Dict[int, int])])
    def emit_dict_int_int(ddict):
        return ddict

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_dict_int_int, input_values={'ddict': {'1': 2}})
