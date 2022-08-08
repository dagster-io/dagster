import pytest

from dagster import DagsterTypeCheckDidNotPass, Dict, In, Out, op
from dagster._legacy import execute_solid


def test_typed_python_dict():
    int_to_int = Dict[int, int]

    int_to_int.type_check(None, {1: 1})


def test_typed_python_dict_failure():
    int_to_int = Dict[int, int]

    res = int_to_int.type_check(None, {1: "1"})
    assert not res.success


def test_basic_solid_dict_int_int_output():
    @op(out=Out(Dict[int, int]))
    def emit_dict_int_int():
        return {1: 1}

    assert execute_solid(emit_dict_int_int).output_value() == {1: 1}


def test_basic_solid_dict_int_int_output_faile():
    @op(out=Out(Dict[int, int]))
    def emit_dict_int_int():
        return {1: "1"}

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict_int_int)


def test_basic_solid_dict_int_int_input_pass():
    @op(ins={"ddict": In(Dict[int, int])})
    def emit_dict_int_int(ddict):
        return ddict

    assert execute_solid(emit_dict_int_int, input_values={"ddict": {1: 2}}).output_value() == {1: 2}


def test_basic_solid_dict_int_int_input_fails():
    @op(ins={"ddict": In(Dict[int, int])})
    def emit_dict_int_int(ddict):
        return ddict

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_dict_int_int, input_values={"ddict": {"1": 2}})
