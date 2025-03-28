"""Sample local components for testing validation. Paired with test cases
in integration_tests/integration_test_defs/validation.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from dagster._core.definitions.definitions_class import Definitions
from pydantic import BaseModel, ConfigDict

from dagster_components import (
    Component,
    ComponentLoadContext,
    ResolvableModel,
    ResolvedFrom,
    Resolver,
)


def _inner_error():
    raise Exception("boom")


def _error():
    _inner_error()


class MyComponentModel(ResolvableModel):
    a_string: str
    an_int: int
    throw: bool = False


def _maybe_throw(ctx, throw):
    if throw:
        _error()
    return throw


@dataclass
class MyComponent(Component, ResolvedFrom[MyComponentModel]):
    a_string: str
    an_int: int
    throw: Annotated[bool, Resolver(_maybe_throw)]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "error": _error,
        }


class MyNestedModel(BaseModel):
    a_string: str
    an_int: int

    model_config = ConfigDict(extra="forbid")


class MyNestedComponentSchema(BaseModel):
    nested: dict[str, MyNestedModel]

    model_config = ConfigDict(extra="forbid")


class MyNestedComponent(Component):
    @classmethod
    def get_schema(cls) -> type[MyNestedComponentSchema]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return MyNestedComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
