"""Sample local components for testing validation. Paired with test cases
in integration_tests/components/validation.
"""

from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, component_type
from dagster_components.core.component import ComponentLoadContext
from pydantic import BaseModel
from typing_extensions import Self


class LoadErrorComponentSchema(BaseModel):
    a_string: str


@component_type
class LoadErrorComponent(Component):
    name = "load_error_component"
    params_schema = LoadErrorComponentSchema

    @classmethod
    def load(cls, context: ComponentLoadContext) -> Self:
        context.load_params(cls.params_schema)

        raise Exception("uh oh, something unexpected happened")

        return cls()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
