from dataclasses import dataclass
from typing import Annotated

from dagster_components import Resolvable, Resolver
from dagster_components.resolved.base import _get_annotations, _get_resolver
from pydantic import BaseModel


def test_inheritance_dataclass() -> None:
    @dataclass
    class Base(Resolvable):
        base_field: int

    @dataclass
    class Derived(Base):
        derived_field: str

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_inheritance_pydantic() -> None:
    class Base(BaseModel, Resolvable):
        base_field: int

    class Derived(Base):
        derived_field: str

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_override_dataclass() -> None:
    @dataclass
    class Base(Resolvable):
        value: int

    class CustomResolver(Resolver): ...

    @dataclass
    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    annotations = _get_annotations(Derived)
    assert "value" in annotations
    resolver = _get_resolver(annotations["value"][0], "value")
    assert isinstance(resolver, CustomResolver)
    Derived(value="hi")


def test_override_pydantic() -> None:
    class Base(BaseModel, Resolvable):
        value: int

    class CustomResolver(Resolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]  # pyright: ignore[reportIncompatibleVariableOverride]

    annotations = _get_annotations(Derived)
    assert "value" in annotations
    resolver = _get_resolver(annotations["value"][0], "value")
    assert isinstance(resolver, CustomResolver)
