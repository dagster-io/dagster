from dataclasses import dataclass
from typing import Annotated

from dagster_components.components.pipes_subprocess_script_collection import DSLFieldResolver
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


def test_override_vanilla() -> None:
    class Base(ResolutionSpec):
        value: int

    class CustomResolver(DSLFieldResolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]

    resolvers = get_annotation_field_resolvers(Derived)
    assert "value" in resolvers
    assert isinstance(resolvers["value"], CustomResolver)


def test_override_dataclass() -> None:
    @dataclass
    class Base(ResolutionSpec):
        value: int

    class CustomResolver(DSLFieldResolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]

    resolvers = get_annotation_field_resolvers(Derived)
    assert "value" in resolvers
    assert isinstance(resolvers["value"], CustomResolver)


def test_override_pydantic() -> None:
    class Base(BaseModel, ResolutionSpec):
        value: int

    class CustomResolver(DSLFieldResolver): ...

    class Derived(Base):
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]

    resolvers = get_annotation_field_resolvers(Derived)
    assert "value" in resolvers
    assert isinstance(resolvers["value"], CustomResolver)
