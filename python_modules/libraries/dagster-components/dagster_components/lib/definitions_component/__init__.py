from pathlib import Path
from typing import Optional

from dagster import DagsterInvalidDefinitionError, Definitions

from dagster_components import Component, ComponentLoadContext, Model, Resolvable
from dagster_components.core.defs_module import DagsterDefsComponent

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
