from collections.abc import Sequence
from typing import Annotated, Optional

import pytest
from dagster._check.functions import ParameterCheckError
from dagster_components import FieldResolver, ResolutionContext, ResolvableSchema
from pydantic import BaseModel


def resolve_val1(context: ResolutionContext, _type: type, schema: "InnerSchema") -> int:
    return context.resolve_value(schema.val1, as_type=int) + 20


class InnerObject(BaseModel):
    val1_renamed: Annotated[int, FieldResolver(resolve_val1)]
    val2: Optional[str]


class TargetObject(BaseModel):
    int_val: int
    str_val: str
    inners: Optional[Sequence[InnerObject]]


class InnerSchema(ResolvableSchema[InnerObject]):
    val1: str
    val2: Optional[str]
    val3: str = "val3"


class TargetSchema(ResolvableSchema[TargetObject]):
    int_val: str
    str_val: str
    inners: Optional[Sequence[InnerSchema]] = None


def test_valid_resolution_simple() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = InnerSchema(val1="{{ some_int }}", val2="{{ some_str }}_b")
    assert context.resolve_value(params) == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = TargetSchema(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[InnerSchema(val1="{{ some_int }}", val2="{{ some_str }}_y")],
    )

    assert context.resolve_value(params) == TargetObject(
        int_val=1,
        str_val="a_x",
        inners=[InnerObject(val1_renamed=21, val2="a_y")],
    )


@pytest.mark.skip("Figure out better way of handling type issues")
def test_invalid_resolution_simple() -> None:
    with pytest.raises(ParameterCheckError):
        context = ResolutionContext(scope={"some_int": "NOT_AN_INT"})
        context.resolve_value(InnerSchema(val1="{{ some_int }}", val2="abc"))
