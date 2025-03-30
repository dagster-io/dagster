from dataclasses import dataclass
from typing import Callable

from dagster._core.definitions.definitions_class import Definitions
from typing_extensions import TypeAlias

from dagster_components.component.component import Component
from dagster_components.component.component_loader import ComponentLoadFn, component
from dagster_components.core.context import ComponentLoadContext

DefinitionsLoadFn: TypeAlias = Callable[[ComponentLoadContext], Definitions]


@dataclass(frozen=True)
class DecoratorDefinitionsComponent(Component):
    fn: DefinitionsLoadFn

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return self.fn(context)


def definitions_component(fn: DefinitionsLoadFn) -> ComponentLoadFn:
    @component
    def load(context: ComponentLoadContext) -> DecoratorDefinitionsComponent:
        return DecoratorDefinitionsComponent(fn)

    return load
