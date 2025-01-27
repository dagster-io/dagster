from collections.abc import Sequence
from typing import Annotated, Optional, Union

import pytest
from dagster._record import record
from dagster_components import ResolvableFieldInfo, ResolvableModel, TemplatedValueResolver
from pydantic import ValidationError


@record
class InnerObject:
    val1: int
    val2: Optional[str]


@record
class TargetObject:
    int_val: int
    str_val: str
    inners: Optional[Sequence[InnerObject]]


class InnerParams(ResolvableModel[InnerObject]):
    val1: Annotated[Union[int, str], ResolvableFieldInfo(output_type=int)]
    val2: Optional[str]

    def resolve(self, resolver: TemplatedValueResolver) -> InnerObject:
        resolved_properties = self._resolved_properties(resolver)
        return InnerObject(val1=resolved_properties["val1"], val2=resolved_properties["val2"])


class TargetParams(ResolvableModel[TargetObject]):
    int_val: Annotated[str, ResolvableFieldInfo(output_type=int)]
    str_val: str
    inners: Annotated[
        Optional[Sequence[InnerParams]],
        ResolvableFieldInfo(output_type=Optional[Sequence[InnerObject]]),
    ] = None

    def resolve(self, resolver: TemplatedValueResolver) -> TargetObject:
        resolved_properties = self._resolved_properties(resolver)
        return TargetObject(
            int_val=resolved_properties["int_val"],
            str_val=resolved_properties["str_val"],
            inners=[inner.resolve(resolver) for inner in self.inners] if self.inners else None,
        )


def test_valid_resolution_simple() -> None:
    resolved = InnerParams(val1="{{ some_int }}", val2="{{ some_str }}_b").resolve(
        TemplatedValueResolver(scope={"some_int": 1, "some_str": "a"})
    )

    assert resolved == InnerObject(val1=1, val2="a_b")


def test_valid_resolution_nested() -> None:
    resolved = TargetParams(
        int_val="{{ some_int }}",
        str_val="{{ some_str }}_x",
        inners=[InnerParams(val1="{{ some_int }}", val2="{{ some_str }}_y")],
    ).resolve(TemplatedValueResolver(scope={"some_int": 1, "some_str": "a"}))

    assert resolved == TargetObject(
        int_val=1,
        str_val="a_x",
        inners=[InnerObject(val1=1, val2="a_y")],
    )


def test_invalid_resolution_simple() -> None:
    with pytest.raises(ValidationError):
        InnerParams(val1="{{ some_int }}", val2="abc").resolve(
            TemplatedValueResolver(scope={"some_int": "NOT_AN_INT"})
        )
