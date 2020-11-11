import pytest
from dagster import lambda_solid, solid
from dagster.core.errors import DagsterInvalidDefinitionError


def test_single_input():
    @solid
    def add_one(_context, num):
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == "num"
    assert add_one.input_defs[0].dagster_type.unique_name == "Any"


def test_double_input():
    @solid
    def subtract(_context, num_one, num_two):
        return num_one + num_two

    assert subtract
    assert len(subtract.input_defs) == 2
    assert subtract.input_defs[0].name == "num_one"
    assert subtract.input_defs[0].dagster_type.unique_name == "Any"

    assert subtract.input_defs[1].name == "num_two"
    assert subtract.input_defs[1].dagster_type.unique_name == "Any"


def test_solid_arg_fails():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Solid functions should only have keyword arguments that match input names and a first positional parameter named 'context'",
    ):

        @solid
        def _other_fails(_other):
            pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Solid functions should only have keyword arguments that match input names and a first positional parameter named 'context'",
    ):

        @solid
        def _empty_fails():
            pass


def test_noop_lambda_solid():
    @lambda_solid
    def noop():
        pass

    assert noop
    assert len(noop.input_defs) == 0
    assert len(noop.output_defs) == 1


def test_one_arg_lambda_solid():
    @lambda_solid
    def one_arg(num):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == "num"
    assert one_arg.input_defs[0].dagster_type.unique_name == "Any"
    assert len(one_arg.output_defs) == 1
