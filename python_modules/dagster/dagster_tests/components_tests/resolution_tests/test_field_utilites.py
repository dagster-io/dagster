from dataclasses import dataclass
from typing import Annotated

import dagster as dg
from dagster.components.resolved.base import _get_annotations, _get_resolver
from pydantic import BaseModel


def test_inheritance_dataclass() -> None:
    @dataclass
    class Base(dg.Resolvable):
        base_field: int

    @dataclass
    class Derived(Base):
        derived_field: str

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_inheritance_pydantic() -> None:
    class Base(BaseModel, dg.Resolvable):
        base_field: int

    class Derived(Base):
        derived_field: str

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_override_dataclass() -> None:
    @dataclass
    class Base(dg.Resolvable):
        value: int

    class CustomResolver(dg.Resolver): ...

    @dataclass
    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    annotations = _get_annotations(Derived)
    assert "value" in annotations
    resolver = _get_resolver(annotations["value"].type, "value")
    assert isinstance(resolver, CustomResolver)
    Derived(value="hi")


def test_override_pydantic() -> None:
    class Base(BaseModel, dg.Resolvable):
        value: int

    class CustomResolver(dg.Resolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    annotations = _get_annotations(Derived)
    assert "value" in annotations
    resolver = _get_resolver(annotations["value"].type, "value")
    assert isinstance(resolver, CustomResolver)
