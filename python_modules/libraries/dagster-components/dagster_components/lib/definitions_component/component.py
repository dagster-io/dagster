import importlib
from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._utils import pushd
from pydantic import Field
from pydantic.dataclasses import dataclass

from dagster_components import (
    Component,
    ComponentLoadContext,
    ResolvableSchema,
    registered_component_type,
)
from dagster_components.lib.definitions_component.scaffolder import DefinitionsComponentScaffolder


class DefinitionsParamSchema(ResolvableSchema):
    definitions_path: Optional[str] = None


@registered_component_type(name="definitions")
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
        with pushd(str(context.path)):
            abs_context_path = context.path.absolute()

            component_module_relative_path = abs_context_path.parts[
                abs_context_path.parts.index("components") + 1 :
            ]
            component_module_name = ".".join([context.module_name, *component_module_relative_path])

            defs_file_path = (
                Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
            ).absolute()
            if defs_file_path.name != "__init__.py":
                component_module_name = f"{component_module_name}.{defs_file_path.stem}"

            module = importlib.import_module(component_module_name)

        return load_definitions_from_module(module)
