from dataclasses import dataclass

from dagster_components.core.schema.resolvable_from_schema import (
    ResolutionSpec,
    get_annotation_field_resolvers,
)
from pydantic import BaseModel


def test_inheritance_vanilla() -> None:
    class Base(ResolutionSpec):
        base_field: int

    class Derived(Base):
        derived_field: str

    resolvers = get_annotation_field_resolvers(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_inheritance_dataclass() -> None:
    @dataclass
    class Base(ResolutionSpec):
        base_field: int

    @dataclass
    class Derived(Base):
        derived_field: str

    resolvers = get_annotation_field_resolvers(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers


def test_inheritance_pydantic() -> None:
    class Base(BaseModel, ResolutionSpec):
        base_field: int

    class Derived(Base):
        derived_field: str

    resolvers = get_annotation_field_resolvers(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers
