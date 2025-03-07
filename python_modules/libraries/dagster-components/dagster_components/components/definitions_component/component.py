from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from pydantic import Field

from dagster_components import Component, ComponentLoadContext
from dagster_components.components.definitions_component.scaffolder import (
    DefinitionsComponentScaffolder,
)
from dagster_components.resolved.model import ResolvableModel
from dagster_components.scaffoldable.decorator import scaffoldable


@scaffoldable(scaffolder=DefinitionsComponentScaffolder)
class DefinitionsComponent(Component, ResolvableModel):
    """Wraps an arbitrary set of Dagster definitions."""

    definitions_path: Optional[str] = Field(
        None, description="Relative path to a file containing Dagster definitions."
    )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs_path = Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
        defs_module = context.load_component_relative_python_module(defs_path)
        defs_attrs = list(find_objects_in_module_of_types(defs_module, Definitions))
        if len(defs_attrs) > 1:
            raise ValueError(
                f"Found multiple Definitions objects in {defs_path}. "
                "At most one Definitions object may be specified when using the DefinitionsComponent."
            )
        elif len(defs_attrs) == 1:
            return defs_attrs[0]
        else:
            return load_definitions_from_module(defs_module)
