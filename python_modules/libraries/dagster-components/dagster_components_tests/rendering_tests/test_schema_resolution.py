from collections.abc import Sequence
from typing import Annotated, Optional, Union

import pytest
from dagster._check.functions import ParameterCheckError
from dagster._record import record
from dagster_components import ResolvableFieldInfo, ResolvableModel, ResolveContext


@record
class InnerObject:
    val1_renamed: int
    val2: Optional[str]


@record
class TargetObject:
    int_val: int
    str_val_renamed: str
    inners: Optional[Sequence[InnerObject]]


class InnerParams(ResolvableModel):
    val1: Annotated[
        Union[int, str], ResolvableFieldInfo(output_type=int, resolved_field_name="val1_renamed")
    ]
    val2: Optional[str]

    def resolve_val1_renamed(self, context: ResolveContext) -> int:
        resolved_val = context.resolve_value(self.val1)
        return resolved_val + 20

    def resolve(self, context: ResolveContext) -> InnerObject:
        return self.resolve_as(InnerObject, context)


class TargetParams(ResolvableModel):
    int_val: Annotated[str, ResolvableFieldInfo(output_type=int)]
    str_val: Annotated[str, ResolvableFieldInfo(resolved_field_name="str_val_renamed")]
    inners: Annotated[
        Optional[Sequence[InnerParams]],
        ResolvableFieldInfo(output_type=Optional[Sequence[InnerObject]]),
    ] = None

    def resolve(self, context: ResolveContext) -> TargetObject:
        return self.resolve_as(TargetObject, context)


def test_valid_resolution_simple() -> None:
    resolved = InnerParams(val1="{{ some_int }}", val2="{{ some_str }}_b").resolve(
        ResolveContext(scope={"some_int": 1, "some_str": "a"})
    )

    assert resolved == InnerObject(val1_renamed=21, val2="a_b")


def test_valid_resolution_nested() -> None:
    resolved = TargetParams(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[InnerParams(val1="{{ some_int }}", val2="{{ some_str }}_y")],
    ).resolve(ResolveContext(scope={"some_int": 1, "some_str": "a"}))

    assert resolved == TargetObject(
        int_val=1,
        str_val_renamed="a_x",
        inners=[InnerObject(val1_renamed=21, val2="a_y")],
    )


@pytest.mark.skip("Figure out better way of handling type issues")
def test_invalid_resolution_simple() -> None:
    with pytest.raises(ParameterCheckError):
        InnerParams(val1="{{ some_int }}", val2="abc").resolve(
            ResolveContext(scope={"some_int": "NOT_AN_INT"})
        )
