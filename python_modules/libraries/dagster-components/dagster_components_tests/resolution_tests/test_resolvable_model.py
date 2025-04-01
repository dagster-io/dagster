from collections.abc import Sequence
from typing import Annotated, Optional

from dagster_components import Injectable, ResolutionContext, Resolvable, Resolver
from pydantic import BaseModel


def resolve_val1(context: ResolutionContext, val1) -> int:
    return context.resolve_value(val1, as_type=int) + 20


class InnerObject(BaseModel, Resolvable):
    val1_renamed: Annotated[
        int,
        Resolver(
            resolve_val1,
            model_field_type=str,
            model_field_name="val1",
        ),
    ]
    val2: Optional[str]


class TargetObject(BaseModel, Resolvable):
    int_val: Injectable[int]
    str_val: str
    inners: Optional[Sequence[InnerObject]]


def test_valid_resolution_simple() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    inner_schema = InnerObject.model()(
        val1="{{ some_int }}",
        val2="{{ some_str }}_b",
    )
    inner = InnerObject.resolve_from_model(context, inner_schema)
    assert inner == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = TargetObject.model()(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[
            InnerObject.model()(
                val1="{{ some_int }}",
                val2="{{ some_str }}_y",
            )
        ],
    )

    target = TargetObject.resolve_from_model(context, params)

    assert target == TargetObject(
        int_val=1,
        str_val="a_x",
        inners=[InnerObject(val1_renamed=21, val2="a_y")],
    )
