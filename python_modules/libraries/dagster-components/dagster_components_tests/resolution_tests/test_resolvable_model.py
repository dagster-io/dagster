from collections.abc import Sequence
from typing import Optional

import pytest
from dagster._check.functions import ParameterCheckError
from dagster._record import record
from dagster_components import ResolutionContext, ResolvableModel
from dagster_components.core.schema.base import Resolver, resolver


@record
class InnerObject:
    val1_renamed: int
    val2: Optional[str]


@record
class TargetObject:
    int_val: int
    str_val: str
    inners: Optional[Sequence[InnerObject]]


class InnerParams(ResolvableModel):
    val1: str
    val2: Optional[str]


class TargetParams(ResolvableModel):
    int_val: str
    str_val: str
    inners: Optional[Sequence[InnerParams]] = None


@resolver(
    fromtype=InnerParams,
    totype=InnerObject,
    exclude_fields={"val1"},
    additional_fields={"val1_renamed"},
)
class InnerParamsResolver(Resolver[InnerParams]):
    def resolve_val1_renamed(self, context: ResolutionContext) -> int:
        return context.resolve_value(self.model.val1) + 20


@resolver(fromtype=TargetParams, totype=TargetObject)
class TargetParamsResolver(Resolver): ...


def test_valid_resolution_simple() -> None:
    resolved = InnerParams(val1="{{ some_int }}", val2="{{ some_str }}_b").resolve(
        ResolutionContext(scope={"some_int": 1, "some_str": "a"})
    )

    assert resolved == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    resolved = TargetParams(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[InnerParams(val1="{{ some_int }}", val2="{{ some_str }}_y")],
    ).resolve(ResolutionContext(scope={"some_int": 1, "some_str": "a"}))

    assert resolved == TargetObject(
        int_val=1,
        str_val="a_x",
        inners=[InnerObject(val1_renamed=21, val2="a_y")],
    )


@pytest.mark.skip("Figure out better way of handling type issues")
def test_invalid_resolution_simple() -> None:
    with pytest.raises(ParameterCheckError):
        InnerParams(val1="{{ some_int }}", val2="abc").resolve(
            ResolutionContext(scope={"some_int": "NOT_AN_INT"})
        )
