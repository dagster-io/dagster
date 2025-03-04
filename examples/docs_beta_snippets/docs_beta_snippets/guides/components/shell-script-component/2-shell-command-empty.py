from dagster import Definitions
from dagster_components import (
    Component,
    ComponentLoadContext,
    DefaultComponentScaffolder,
)
from dagster_components.core.schema.base import PlainSamwiseSchema

class ShellCommandSchema(PlainSamwiseSchema):
    ...

class ShellCommand(Component):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    @classmethod
    def get_schema(cls):
        return ShellCommandSchema

    def build_defs(self, load_context: ComponentLoadContext) -> Definitions:
        # Add definition construction logic here.
        return Definitions()
