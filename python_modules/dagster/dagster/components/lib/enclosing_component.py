from abc import abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any

from dagster import Resolvable
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.model import Model


def merge_component_defs(
    context: ComponentLoadContext, components: Iterable[Component]
) -> Definitions:
    return Definitions.merge(*[component.build_defs(context) for component in components])


class EnclosingComponent(Component, Resolvable, Model):
    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return merge_component_defs(context, self.build_components(context)).with_resources(
            self.resources()
        )

    @abstractmethod
    def build_components(self, context: ComponentLoadContext) -> Iterable[Component]: ...

    def resources(self) -> Mapping[str, Any]:
        return {}
