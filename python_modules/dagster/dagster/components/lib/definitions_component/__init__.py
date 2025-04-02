from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import DagsterDefsComponent
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Model

############
# BACKCOMPAT
############


class DefinitionsComponent(Component, Model, Resolvable):
    """An arbitrary set of dagster definitions."""

    path: Optional[str]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        inner_context = context.for_path(Path(self.path)) if self.path else context
        component = DagsterDefsComponent.from_context(inner_context)
        if component is None:
            raise DagsterInvalidDefinitionError(
                f"Could not resolve {self.path} to a DagsterDefsComponent."
            )
        return component.build_defs(context)
