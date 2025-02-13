from collections.abc import Sequence
from typing import Optional

import pytest
from dagster._check.functions import ParameterCheckError
from dagster_components import ResolutionContext, ResolvableSchema, field_resolver
from pydantic import BaseModel


class InnerObject(BaseModel):
    val1_renamed: int
    val2: Optional[str]

    @field_resolver("val1_renamed")
    @staticmethod
    def resolve_val1_renamed(context: ResolutionContext, schema: "InnerSchema") -> int:
        return 20 + context.resolve_value(schema.val1, as_type=int)


class TargetObject(BaseModel):
    int_val: int
    str_val: str
    inners: Optional[Sequence[InnerObject]]


class InnerSchema(ResolvableSchema[InnerObject]):
    val1: str
    val2: Optional[str]


class TargetParams(ResolvableSchema[TargetObject]):
    int_val: str
    str_val: str
    inners: Optional[Sequence[InnerSchema]] = None


def test_valid_resolution_simple() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = InnerSchema(val1="{{ some_int }}", val2="{{ some_str }}_b")
    assert context.resolve_value(params) == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = TargetParams(
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
