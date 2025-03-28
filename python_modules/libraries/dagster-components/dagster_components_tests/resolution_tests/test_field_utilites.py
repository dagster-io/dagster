from dataclasses import dataclass
from typing import Annotated

from dagster_components.resolved.model import (
    ResolvedKwargs,
    Resolver,
    get_annotation_field_resolvers,
)
from pydantic import BaseModel


def test_inheritance_vanilla() -> None:
    class Base(ResolvedKwargs):
        base_field: int

    class Derived(Base):
        derived_field: str

    resolvers = get_annotation_field_resolvers(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_inheritance_dataclass() -> None:
    @dataclass
    class Base(ResolvedKwargs):
        base_field: int

    @dataclass
    class Derived(Base):
        derived_field: str

    resolvers = get_annotation_field_resolvers(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_inheritance_pydantic() -> None:
    class Base(BaseModel, ResolvedKwargs):
        base_field: int

    class Derived(Base):
        derived_field: str

    resolvers = get_annotation_field_resolvers(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_override_vanilla() -> None:
    class Base(ResolvedKwargs):
        value: int

    class CustomResolver(Resolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    resolvers = get_annotation_field_resolvers(Derived)
    assert "value" in resolvers
    assert isinstance(resolvers["value"], CustomResolver)


def test_override_dataclass() -> None:
    @dataclass
    class Base(ResolvedKwargs):
        value: int

    class CustomResolver(Resolver): ...

    @dataclass
    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    resolvers = get_annotation_field_resolvers(Derived)
    assert "value" in resolvers
    assert isinstance(resolvers["value"], CustomResolver)
    Derived(value="hi")


def test_override_pydantic() -> None:
    class Base(BaseModel, ResolvedKwargs):
        value: int

    class CustomResolver(Resolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    resolvers = get_annotation_field_resolvers(Derived)
    assert "value" in resolvers
    assert isinstance(resolvers["value"], CustomResolver)
