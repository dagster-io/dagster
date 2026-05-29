from dataclasses import dataclass
from typing import Annotated, ClassVar

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


def test_inheritance_dataclass_without_redecoration() -> None:
    # A subclass that adds a field without re-applying @dataclass should still pick up the
    # new field, matching how pydantic Model subclasses behave. See
    # https://github.com/dagster-io/dagster/issues/33889.
    @dataclass
    class Base(dg.Resolvable):
        base_field: int

    class Derived(Base):
        derived_field: str = "default"

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers

    # the new field resolves end-to-end (and the yaml value wins over the class default)
    resolved = Derived.resolve_from_dict({"base_field": 1, "derived_field": "from_yaml"})
    assert resolved.base_field == 1
    assert resolved.derived_field == "from_yaml"


def test_inheritance_dataclass_classvar_not_treated_as_field() -> None:
    @dataclass
    class Base(dg.Resolvable):
        base_field: int

    class Derived(Base):
        not_a_field: ClassVar[str] = "constant"

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "not_a_field" not in resolvers


def test_inheritance_frozen_dataclass_without_redecoration() -> None:
    @dataclass(frozen=True)
    class Base(dg.Resolvable):
        base_field: int

    class Derived(Base):
        derived_field: str = "default"

    resolvers = _get_annotations(Derived)
    assert "base_field" in resolvers
    assert "derived_field" in resolvers

    resolved = Derived.resolve_from_dict({"base_field": 1, "derived_field": "from_yaml"})
    assert resolved.derived_field == "from_yaml"


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
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]

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
        value: Annotated[str, CustomResolver(lambda context, val: str(val))]

    annotations = _get_annotations(Derived)
    assert "value" in annotations
    resolver = _get_resolver(annotations["value"].type, "value")
    assert isinstance(resolver, CustomResolver)
