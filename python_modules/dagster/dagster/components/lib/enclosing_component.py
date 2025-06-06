from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Optional

from dagster import Resolvable
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import AssetPostProcessor, post_process_defs
from dagster.components.resolved.model import Model


def merge_component_defs(
    context: ComponentLoadContext, components: Iterable[Component]
) -> Definitions:
    return Definitions.merge(*[component.build_defs(context) for component in components])


class EnclosingComponent(Component, Resolvable, Model):
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return post_process_defs(
            merge_component_defs(context, self.build_components(context)),
            self.asset_post_processors,
        ).with_resources(self.resources())

    @abstractmethod
    def build_components(self, context: ComponentLoadContext) -> Iterable[Component]: ...

    def resources(self) -> Mapping[str, Any]:
        return {}
