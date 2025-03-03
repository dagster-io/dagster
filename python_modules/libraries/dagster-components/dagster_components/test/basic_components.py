"""Sample local components for testing validation. Paired with test cases
in integration_tests/components/validation.
"""

from dataclasses import dataclass

from dagster._core.definitions.definitions_class import Definitions
from pydantic import BaseModel, ConfigDict

from dagster_components import Component
from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.schema.base import PlainSamwiseSchema


class MyComponentSchema(PlainSamwiseSchema):
    a_string: str
    an_int: int


@dataclass
class MyComponent(Component):
    a_string: str
    an_int: int

    @classmethod
    def get_schema(cls) -> type[MyComponentSchema]:
        return MyComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


class MyNestedModel(BaseModel):
    a_string: str
    an_int: int

    model_config = ConfigDict(extra="forbid")


class MyNestedComponentSchema(BaseModel):
    nested: dict[str, MyNestedModel]

    model_config = ConfigDict(extra="forbid")


class MyNestedComponent(Component):
    @classmethod
    def get_schema(cls) -> type[MyNestedComponentSchema]:
        return MyNestedComponentSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
