from typing import Tuple

import pytest

from dagster import (
    DagsterTypeCheckError,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)
from dagster.core.types.python_tuple import create_typed_tuple


def test_vanilla_tuple_output():
    @lambda_solid(output_def=OutputDefinition(tuple))
    def emit_tuple():
        return (1, 2)

    assert execute_solid(emit_tuple).output_value() == (1, 2)


def test_vanilla_tuple_output_fail():
    @lambda_solid(output_def=OutputDefinition(tuple))
    def emit_tuple():
        return 'foo'

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_tuple)


def test_vanilla_tuple_input():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=tuple)])
    def take_tuple(tt):
        return tt

    assert execute_solid(take_tuple, input_values={'tt': (2, 3)}).output_value() == (2, 3)


def test_vanilla_tuple_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=tuple)])
    def take_tuple(tt):
        return tt

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(take_tuple, input_values={'tt': 'fkjdf'})


def test_open_typing_tuple_output():
    @lambda_solid(output_def=OutputDefinition(Tuple))
    def emit_tuple():
        return (1, 2)

    assert execute_solid(emit_tuple).output_value() == (1, 2)


def test_open_typing_tuple_output_fail():
    @lambda_solid(output_def=OutputDefinition(Tuple))
    def emit_tuple():
        return 'foo'

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_tuple)


def test_open_typing_tuple_input():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=Tuple)])
    def take_tuple(tt):
        return tt

    assert execute_solid(take_tuple, input_values={'tt': (2, 3)}).output_value() == (2, 3)


def test_open_typing_tuple_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=Tuple)])
    def take_tuple(tt):
        return tt

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(take_tuple, input_values={'tt': 'fkjdf'})


def test_typed_python_tuple_directly():
    int_str_tuple = create_typed_tuple(int, str).inst()

    int_str_tuple.type_check((1, 'foo'))

    res = int_str_tuple.type_check(None)
    assert not res.success

    res = int_str_tuple.type_check('bar')
    assert not res.success

    res = int_str_tuple.type_check((1, 2, 3))
    assert not res.success

    res = int_str_tuple.type_check(('1', 2))
    assert not res.success


def test_nested_python_tuple_directly():
    int_str_tuple_kls = create_typed_tuple(int, str)

    nested_tuple = create_typed_tuple(bool, list, int_str_tuple_kls).inst()

    nested_tuple.type_check((True, [1], (1, 'foo')))

    res = nested_tuple.type_check(None)
    assert not res.success

    res = nested_tuple.type_check('bar')
    assert not res.success

    res = nested_tuple.type_check((True, [1], (1, 2)))
    assert not res.success


def test_closed_typing_tuple_output():
    @lambda_solid(output_def=OutputDefinition(Tuple[int, int]))
    def emit_tuple():
        return (1, 2)

    assert execute_solid(emit_tuple).output_value() == (1, 2)


def test_closed_typing_tuple_output_fail():
    @lambda_solid(output_def=OutputDefinition(Tuple[int, int]))
    def emit_tuple():
        return 'foo'

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_tuple)


def test_closed_typing_tuple_output_fail_wrong_member_types():
    @lambda_solid(output_def=OutputDefinition(Tuple[int, int]))
    def emit_tuple():
        return (1, 'nope')

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_tuple)


def test_closed_typing_tuple_output_fail_wrong_length():
    @lambda_solid(output_def=OutputDefinition(Tuple[int, int]))
    def emit_tuple():
        return (1,)

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_tuple)


def test_closed_typing_tuple_input():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=Tuple[int, int])])
    def take_tuple(tt):
        return tt

    assert execute_solid(take_tuple, input_values={'tt': (2, 3)}).output_value() == (2, 3)


def test_closed_typing_tuple_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=Tuple[int, int])])
    def take_tuple(tt):
        return tt

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(take_tuple, input_values={'tt': 'fkjdf'})
