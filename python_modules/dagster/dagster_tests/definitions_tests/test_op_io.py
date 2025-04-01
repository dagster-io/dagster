import sys
from collections.abc import Generator, Iterator
from typing import (  # noqa:UP035
    Iterable as TypingIterable,
    Iterator as TypingIterator,
)

import pytest
from dagster import AssetKey, DynamicOut, DynamicOutput, In, Out, Output, op
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._legacy import InputDefinition, OutputDefinition


def test_flex_inputs():
    @op(ins={"arg_b": In(metadata={"explicit": True})})
    def partial(_context, arg_a, arg_b):
        return arg_a + arg_b

    assert partial.input_defs[0].name == "arg_b"
    assert partial.input_defs[0].metadata["explicit"]
    assert partial.input_defs[1].name == "arg_a"


def test_merge_type():
    @op(ins={"arg_b": In(metadata={"explicit": True})})
    def merged(_context, arg_b: int):
        return arg_b

    assert (
        merged.input_defs[0].dagster_type == InputDefinition("test", dagster_type=int).dagster_type
    )
    assert merged.input_defs[0].metadata["explicit"]


def test_merge_desc():
    @op(ins={"arg_b": In(metadata={"explicit": True})})
    def merged(_context, arg_a, arg_b, arg_c):
        """Testing.

        Args:
            arg_b: described
        """
        return arg_a + arg_b + arg_c

    assert merged.input_defs[0].name == "arg_b"
    assert merged.input_defs[0].description == "described"
    assert merged.input_defs[0].metadata["explicit"]


def test_merge_default_val():
    @op(ins={"arg_b": In(dagster_type=int, metadata={"explicit": True})})
    def merged(_context, arg_a: int, arg_b=3, arg_c=0):
        return arg_a + arg_b + arg_c

    assert merged.input_defs[0].name == "arg_b"
    assert merged.input_defs[0].default_value == 3
    assert (
        merged.input_defs[0].dagster_type == InputDefinition("test", dagster_type=int).dagster_type
    )


def test_precedence():
    @op(
        ins={
            "arg_b": In(
                dagster_type=str,
                default_value="hi",
                description="legit",
                metadata={"explicit": True},
                input_manager_key="rudy",
                asset_key=AssetKey("table_1"),
                asset_partitions={"0"},
            )
        }
    )
    def precedence(_context, arg_a: int, arg_b: int, arg_c: int):
        """Testing.

        Args:
            arg_b: boo
        """
        return arg_a + arg_b + arg_c

    assert precedence.input_defs[0].name == "arg_b"
    assert (
        precedence.input_defs[0].dagster_type
        == InputDefinition("test", dagster_type=str).dagster_type
    )
    assert precedence.input_defs[0].description == "legit"
    assert precedence.input_defs[0].default_value == "hi"
    assert precedence.input_defs[0].metadata["explicit"]
    assert precedence.input_defs[0].input_manager_key == "rudy"
    assert precedence.input_defs[0].get_asset_key(None) is not None  # pyright: ignore[reportArgumentType]
    assert precedence.input_defs[0].get_asset_partitions(None) is not None  # pyright: ignore[reportArgumentType]


def test_output_merge():
    @op(out={"four": Out()})
    def foo(_) -> int:
        return 4

    assert foo.output_defs[0].name == "four"
    assert foo.output_defs[0].dagster_type == OutputDefinition(int).dagster_type


def test_iter_out():
    @op(out={"A": Out()})
    def _ok(_) -> Iterator[Output]:
        yield Output("a", output_name="A")

    @op
    def _also_ok(_) -> Iterator[Output]:
        yield Output("a", output_name="A")

    @op
    def _gen_too(_) -> Generator[Output, None, None]:
        yield Output("a", output_name="A")

    @op(out={"A": Out(), "B": Out()})
    def _multi_fine(_) -> Iterator[Output]:
        yield Output("a", output_name="A")
        yield Output("b", output_name="B")


def test_dynamic():
    @op(out=DynamicOut(dagster_type=int))
    def dyn_desc(_) -> Iterator[DynamicOutput]:
        """
        Returns:
            numbers.
        """  # noqa: D212
        yield DynamicOutput(4, "4")

    assert dyn_desc.output_defs[0].description == "numbers."
    assert dyn_desc.output_defs[0].is_dynamic


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason=(
        "typing types isinstance of type in py3.6,"
        " https://github.com/dagster-io/dagster/issues/4077"
    ),
)
def test_not_type_input():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Problem using type '.*' from type annotation for argument 'arg_b', correct the issue"
            r" or explicitly set the dagster_type"
        ),
    ):

        @op
        def _create(
            _context,
            # invalid since Iterator is not a python type or DagsterType
            arg_b: TypingIterator[int],
        ):
            return arg_b

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Problem using type '.*' from type annotation for argument 'arg_b', correct the issue"
            r" or explicitly set the dagster_type"
        ),
    ):

        @op(ins={"arg_b": In()})
        def _combine(
            _context,
            # invalid since Iterator is not a python type or DagsterType
            arg_b: TypingIterator[int],
        ):
            return arg_b

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Problem using type '.*' from return type annotation, correct the issue or explicitly"
            r" set the dagster_type"
        ),
    ):

        @op
        def _out(_context) -> TypingIterable[int]:
            return [1]
