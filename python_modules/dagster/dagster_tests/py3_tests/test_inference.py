import pytest

from dagster import (
    lambda_solid,
    solid,
    composite_solid,
    DagsterInvalidDefinitionError,
    Int,
    InputDefinition,
    dagster_type,
)
from typing import List, Optional, Any, Union


def test_single_typed_input():
    @solid
    def add_one_infer(_context, num: int):
        return num + 1

    @solid(inputs=[InputDefinition('num', Int)])
    def add_one_ex(_context, num):
        return num + 1

    assert len(add_one_infer.input_defs) == 1

    assert add_one_ex.input_defs[0].name == add_one_infer.input_defs[0].name
    assert (
        add_one_ex.input_defs[0].runtime_type.name == add_one_infer.input_defs[0].runtime_type.name
    )


def test_precedence():
    @solid(inputs=[InputDefinition('num', Int)])
    def add_one(_context, num: Any):
        return num + 1

    assert add_one.input_defs[0].runtime_type.name == 'Int'


def test_double_typed_input():
    @solid
    def add(_context, num_one: int, num_two: int):
        return num_one + num_two

    assert add
    assert len(add.input_defs) == 2
    assert add.input_defs[0].name == 'num_one'
    assert add.input_defs[0].runtime_type.name == 'Int'

    assert add.input_defs[1].name == 'num_two'
    assert add.input_defs[1].runtime_type.name == 'Int'


def test_one_arg_typed_lambda_solid():
    @lambda_solid
    def one_arg(num: int):
        return num

    assert one_arg
    assert len(one_arg.input_defs) == 1
    assert one_arg.input_defs[0].name == 'num'
    assert one_arg.input_defs[0].runtime_type.name == 'Int'
    assert len(one_arg.output_defs) == 1


def test_single_typed_input_and_output():
    @solid
    def add_one(_context, num: int) -> int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].runtime_type.name == 'Int'

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].runtime_type.name == 'Int'


def test_single_typed_input_and_output_lambda():
    @lambda_solid
    def add_one(num: int) -> int:
        return num + 1

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'num'
    assert add_one.input_defs[0].runtime_type.name == 'Int'

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].runtime_type.name == 'Int'


def test_wrapped_input_and_output_lambda():
    @lambda_solid
    def add_one(nums: List[int]) -> Optional[List[int]]:
        return [num + 1 for num in nums]

    assert add_one
    assert len(add_one.input_defs) == 1
    assert add_one.input_defs[0].name == 'nums'
    assert add_one.input_defs[0].runtime_type.is_list
    assert add_one.input_defs[0].runtime_type.inner_type.name == 'Int'

    assert len(add_one.output_defs) == 1
    assert add_one.output_defs[0].runtime_type.is_nullable
    assert add_one.output_defs[0].runtime_type.inner_type.is_list


def test_invalid_function_signatures():
    class Foo:
        pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid
        def _test_non_dagster_class_input(num: Foo):
            return num

    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid
        def _test_non_dagster_class_output() -> Foo:
            return 1

    # Optional[X] is represented as Union[X, NoneType] - test that we throw on other Unions
    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid
        def _test_union_not_optional(num: Union[int, str]):
            return num


def test_kitchen_sink():
    @dagster_type
    class Custom:
        pass

    @lambda_solid
    def sink(
        n: int, f: float, b: bool, s: str, x: Any, o: Optional[str], l: List[str], c: Custom
    ):  # pylint: disable=unused-argument
        pass

    assert sink.input_defs[0].name == 'n'
    assert sink.input_defs[0].runtime_type.name == 'Int'

    assert sink.input_defs[1].name == 'f'
    assert sink.input_defs[1].runtime_type.name == 'Float'

    assert sink.input_defs[2].name == 'b'
    assert sink.input_defs[2].runtime_type.name == 'Bool'

    assert sink.input_defs[3].name == 's'
    assert sink.input_defs[3].runtime_type.name == 'String'

    assert sink.input_defs[4].name == 'x'
    assert sink.input_defs[4].runtime_type.name == 'Any'

    assert sink.input_defs[5].name == 'o'
    assert sink.input_defs[5].runtime_type.is_nullable

    assert sink.input_defs[6].name == 'l'
    assert sink.input_defs[6].runtime_type.is_list

    assert sink.input_defs[7].name == 'c'
    assert sink.input_defs[7].runtime_type.name == 'Custom'


def test_composites():
    @lambda_solid
    def emit_one() -> int:
        return 1

    @lambda_solid
    def add(n1: int, n2: int) -> int:
        return n1 + n2

    @composite_solid
    def add_one(_, a: int) -> int:
        return add(a, emit_one())

    assert add_one.input_mappings
