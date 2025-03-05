from collections.abc import Sequence
from typing import Annotated, Optional

from dagster_components import ResolutionContext
from dagster_components.core.schema.resolvable_from_schema import (
    ResolvableFromSchema,
    YamlFieldResolver,
    YamlSchema,
    resolve_schema_to_resolvable,
)
from pydantic import BaseModel


def resolve_val1(context: ResolutionContext, schema: "InnerSchema") -> int:
    return context.resolve_value(schema.val1, as_type=int) + 20


class InnerObject(BaseModel, ResolvableFromSchema["InnerSchema"]):
    val1_renamed: Annotated[int, YamlFieldResolver.from_parent(resolve_val1)]
    val2: Optional[str]


class TargetObject(BaseModel, ResolvableFromSchema["TargetSchema"]):
    int_val: int
    str_val: str
    inners: Annotated[
        Optional[Sequence[InnerObject]], YamlFieldResolver(InnerObject.from_optional_seq)
    ]


class InnerSchema(YamlSchema):
    val1: str
    val2: Optional[str]
    val3: str = "val3"


class TargetSchema(YamlSchema):
    int_val: str
    str_val: str
    inners: Optional[Sequence[InnerSchema]]


def test_valid_resolution_simple() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    inner_schema = InnerSchema(val1="{{ some_int }}", val2="{{ some_str }}_b")
    inner = resolve_schema_to_resolvable(inner_schema, InnerObject, context)
    assert inner == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    context = ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    params = TargetSchema(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[InnerSchema(val1="{{ some_int }}", val2="{{ some_str }}_y")],
    )

    target = resolve_schema_to_resolvable(params, TargetObject, context)

    assert target == TargetObject(
        int_val=1,
        str_val="a_x",
        inners=[InnerObject(val1_renamed=21, val2="a_y")],
    )
