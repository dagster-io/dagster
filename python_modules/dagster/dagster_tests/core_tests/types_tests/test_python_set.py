import typing

import pytest

from dagster import (
    DagsterTypeCheckError,
    InputDefinition,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)


def test_vanilla_set_output():
    @lambda_solid(output_def=OutputDefinition(set))
    def emit_set():
        return {1, 2}

    assert execute_solid(emit_set).output_value() == {1, 2}


def test_vanilla_set_output_fail():
    @lambda_solid(output_def=OutputDefinition(set))
    def emit_set():
        return 'foo'

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_set)


def test_vanilla_set_input():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=set)])
    def take_set(tt):
        return tt

    assert execute_solid(take_set, input_values={'tt': {2, 3}}).output_value() == {2, 3}


def test_vanilla_set_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=set)])
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(take_set, input_values={'tt': 'fkjdf'})


def test_open_typing_set_output():
    @lambda_solid(output_def=OutputDefinition(typing.Set))
    def emit_set():
        return {1, 2}

    assert execute_solid(emit_set).output_value() == {1, 2}


def test_open_typing_set_output_fail():
    @lambda_solid(output_def=OutputDefinition(typing.Set))
    def emit_set():
        return 'foo'

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(emit_set)


def test_open_typing_set_input():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=typing.Set)])
    def take_set(tt):
        return tt

    assert execute_solid(take_set, input_values={'tt': {2, 3}}).output_value() == {2, 3}


def test_open_typing_set_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name='tt', dagster_type=typing.Set)])
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(take_set, input_values={'tt': 'fkjdf'})
