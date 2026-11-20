from collections.abc import Sequence
from typing import Annotated

import dagster as dg
import pytest
from dagster import ResolutionContext
from dagster.components.resolved.errors import ResolutionException
from pydantic import BaseModel


def resolve_val1(context: ResolutionContext, val1) -> int:
    return context.resolve_value(val1, as_type=int) + 20


class InnerObject(BaseModel, dg.Resolvable):
    val1_renamed: Annotated[
        int,
        dg.Resolver(
            resolve_val1,
            model_field_type=str,
            model_field_name="val1",
            inject_before_resolve=False,
        ),
    ]
    val2: str | None


class TargetObject(BaseModel, dg.Resolvable):
    int_val: int
    str_val: str
    inners: Sequence[InnerObject] | None


def test_valid_resolution_simple() -> None:
    context = dg.ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    inner_schema = InnerObject.model()(
        val1="{{ some_int }}",
        val2="{{ some_str }}_b",
    )
    inner = InnerObject.resolve_from_model(context, inner_schema)
    assert inner == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    context = dg.ResolutionContext(scope={"some_int": 1, "some_str": "a"})
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


def test_resolution_compiles_each_template_once() -> None:
    """Repeated strings reuse one compiled template, and renders keep their own scope."""
    from dagster.components.resolved.context import _native_template

    _native_template.cache_clear()
    assert dg.ResolutionContext(scope={"x": 1}).resolve_value("{{ x }}") == 1
    assert dg.ResolutionContext(scope={"x": 2}).resolve_value("{{ x }}") == 2
    assert _native_template.cache_info().misses == 1

    # Syntax errors are not cached: every resolution reports them.
    for _ in range(2):
        with pytest.raises(ResolutionException, match="TemplateSyntaxError"):
            dg.ResolutionContext(scope={}).resolve_value("{{ x ")
