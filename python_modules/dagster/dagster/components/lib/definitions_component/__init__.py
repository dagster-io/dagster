from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import DagsterDefsComponent
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Model

############
# BACKCOMPAT
############


class DefinitionsComponent(Component, Model, Resolvable):
    """An arbitrary set of Dagster definitions."""

    path: Optional[str]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        component = DagsterDefsComponent(Path(self.path) if self.path else context.path)
        return component.build_defs(context)
