import dagster as dg

"""Sample local components for testing validation. Paired with test cases
in integration_tests/integration_test_defs/validation.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from dagster.components.core.context import ComponentLoadContext
from pydantic import BaseModel, ConfigDict


def _inner_error():
    raise Exception("boom")


def _error():
    _inner_error()


def _maybe_throw(ctx, throw):
    if throw:
        _error()
    return throw


@dataclass
class MyComponent(dg.Component, dg.Resolvable):
    a_string: str
    an_int: int
    throw: Annotated[bool, dg.Resolver(_maybe_throw)] = False

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {
            "error": _error,
        }


class MyNestedModel(BaseModel):
    a_string: str
    an_int: int

    model_config = ConfigDict(extra="forbid")


class MyNestedComponentModel(BaseModel):
    nested: dict[str, MyNestedModel]

    model_config = ConfigDict(extra="forbid")


class MyNestedComponent(dg.Component):
    @classmethod
    def get_model_cls(cls) -> type[MyNestedComponentModel]:
        return MyNestedComponentModel

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
