import typing

import pytest
from dagster import (
    DagsterTypeCheckDidNotPass,
    InputDefinition,
    Optional,
    OutputDefinition,
    execute_solid,
    lambda_solid,
)
from dagster.core.types.dagster_type import resolve_dagster_type
from dagster.core.types.python_set import create_typed_runtime_set


def test_vanilla_set_output():
    @lambda_solid(output_def=OutputDefinition(set))
    def emit_set():
        return {1, 2}

    assert execute_solid(emit_set).output_value() == {1, 2}


def test_vanilla_set_output_fail():
    @lambda_solid(output_def=OutputDefinition(set))
    def emit_set():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_set)


def test_vanilla_set_input():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=set)])
    def take_set(tt):
        return tt

    assert execute_solid(take_set, input_values={"tt": {2, 3}}).output_value() == {2, 3}


def test_vanilla_set_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=set)])
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_set, input_values={"tt": "fkjdf"})


def test_open_typing_set_output():
    @lambda_solid(output_def=OutputDefinition(typing.Set))
    def emit_set():
        return {1, 2}

    assert execute_solid(emit_set).output_value() == {1, 2}


def test_open_typing_set_output_fail():
    @lambda_solid(output_def=OutputDefinition(typing.Set))
    def emit_set():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(emit_set)


def test_open_typing_set_input():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=typing.Set)])
    def take_set(tt):
        return tt

    assert execute_solid(take_set, input_values={"tt": {2, 3}}).output_value() == {2, 3}


def test_open_typing_set_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=typing.Set)])
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_set, input_values={"tt": "fkjdf"})


def test_runtime_set_of_int():
    set_dagster_type = create_typed_runtime_set(int)

    set_dagster_type.type_check(None, {1})
    set_dagster_type.type_check(None, set())

    res = set_dagster_type.type_check(None, None)
    assert not res.success

    res = set_dagster_type.type_check(None, "nope")
    assert not res.success

    res = set_dagster_type.type_check(None, {"nope"})
    assert not res.success


def test_runtime_optional_set():
    set_dagster_type = resolve_dagster_type(Optional[create_typed_runtime_set(int)])

    set_dagster_type.type_check(None, {1})
    set_dagster_type.type_check(None, set())
    set_dagster_type.type_check(None, None)

    res = set_dagster_type.type_check(None, "nope")
    assert not res.success

    res = set_dagster_type.type_check(None, {"nope"})
    assert not res.success


def test_closed_typing_set_input():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=typing.Set[int])])
    def take_set(tt):
        return tt

    assert execute_solid(take_set, input_values={"tt": {2, 3}}).output_value() == {2, 3}


def test_closed_typing_set_input_fail():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=typing.Set[int])])
    def take_set(tt):
        return tt

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_set, input_values={"tt": "fkjdf"})

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_solid(take_set, input_values={"tt": {"fkjdf"}})


def test_typed_set_type_loader():
    @lambda_solid(input_defs=[InputDefinition(name="tt", dagster_type=typing.Set[int])])
    def take_set(tt):
        return tt

    expected_output = set([1, 2, 3, 4])
    assert (
        execute_solid(
            take_set,
            run_config={"solids": {"take_set": {"inputs": {"tt": list(expected_output)}}}},
        ).output_value()
        == expected_output
    )
