import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._utils import pushd

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

    definitions_path: Optional[str]

    @classmethod
    def get_scaffolder(cls) -> DefinitionsComponentScaffolder:
        return DefinitionsComponentScaffolder()

    @classmethod
    def get_schema(cls) -> type[DefinitionsParamSchema]:
        return DefinitionsParamSchema

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        with pushd(str(context.path)):
            component_module_name = ".".join([context.module_name, context.path.stem])

            defs_file_path = (
                Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
            ).absolute()
            if defs_file_path.name != "__init__.py":
                name = f"{component_module_name}.{defs_file_path.stem}"

            module = importlib.import_module(name)

        return load_definitions_from_module(module)
