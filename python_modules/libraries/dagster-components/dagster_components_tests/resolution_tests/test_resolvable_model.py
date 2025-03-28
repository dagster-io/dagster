from collections.abc import Sequence
from typing import Annotated, Optional

from dagster_components import ResolutionContext
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver, resolve_model
from pydantic import BaseModel


def resolve_val1(context: ResolutionContext, schema: "InnerModel") -> int:
    return context.resolve_value(schema.val1, as_type=int) + 20


class InnerObject(BaseModel, ResolvedFrom["InnerModel"]):
    val1_renamed: Annotated[int, Resolver.from_model(resolve_val1)]
    val2: Optional[str]


class TargetObject(BaseModel, ResolvedFrom["TargetModel"]):
    int_val: int
    str_val: str
    inners: Annotated[Optional[Sequence[InnerObject]], Resolver.from_annotation()]


class InnerModel(ResolvableModel):
    val1: str
    val2: Optional[str]
    val3: str = "val3"


class TargetModel(ResolvableModel):
    int_val: str
    str_val: str
    inners: Optional[Sequence[InnerModel]]


def test_valid_resolution_simple() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    inner_schema = InnerModel(val1="{{ some_int }}", val2="{{ some_str }}_b")
    inner = resolve_model(inner_schema, InnerObject, context)
    assert inner == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = TargetModel(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[InnerModel(val1="{{ some_int }}", val2="{{ some_str }}_y")],
    )

    target = resolve_model(params, TargetObject, context)

    assert target == TargetObject(
        int_val=1,
        str_val="a_x",
        inners=[InnerObject(val1_renamed=21, val2="a_y")],
    )
