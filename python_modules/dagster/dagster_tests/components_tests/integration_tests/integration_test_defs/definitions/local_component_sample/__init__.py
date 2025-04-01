from dagster._components import Component, ComponentLoadContext
from dagster._core.definitions.definitions_class import Definitions


class MyComponent(Component):
    a_string: str
    an_int: int

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()
