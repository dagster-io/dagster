from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component import Component, ComponentLoadContext
from dagster_components.resolved.model import ResolvableModel


class SqlComponent(Component, ResolvableModel):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
