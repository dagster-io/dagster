from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from pydantic import Field

from dagster_components import Component, ComponentLoadContext
from dagster_components.components.definitions_component.scaffolder import (
    DefinitionsComponentScaffolder,
)
from dagster_components.core.schema.resolvable_from_schema import YamlSchema
from dagster_components.scaffoldable.decorator import scaffoldable


@scaffoldable(scaffolder=DefinitionsComponentScaffolder)
class DefinitionsComponent(Component, YamlSchema):
    """Wraps an arbitrary set of Dagster definitions."""

    definitions_path: Optional[str] = Field(
        None, description="Relative path to a file containing Dagster definitions."
    )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return load_definitions_from_module(
            context.load_component_relative_python_module(
                Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
            )
        )
