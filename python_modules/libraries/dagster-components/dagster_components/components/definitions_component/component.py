from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from pydantic import Field
from pydantic.dataclasses import dataclass

from dagster_components import Component, ComponentLoadContext, ResolvableSchema
from dagster_components.components.definitions_component.scaffolder import (
    DefinitionsComponentScaffolder,
)


class DefinitionsParamSchema(ResolvableSchema):
    definitions_path: Optional[str] = None


@dataclass
class DefinitionsComponent(Component):
    """Wraps an arbitrary set of Dagster definitions."""

    definitions_path: Optional[str] = Field(
        ..., description="Relative path to a file containing Dagster definitions."
    )

    @classmethod
    def get_scaffolder(cls) -> DefinitionsComponentScaffolder:
        return DefinitionsComponentScaffolder()

    @classmethod
    def get_schema(cls) -> type[DefinitionsParamSchema]:
        return DefinitionsParamSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return load_definitions_from_module(
            context.load_component_relative_python_module(
                Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
            )
        )
