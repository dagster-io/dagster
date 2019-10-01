from typing import Tuple

import pytest

from dagster import (
    DagsterTypeCheckError,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)


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
