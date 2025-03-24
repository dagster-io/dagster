from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from pydantic import Field

from dagster_components.component.component import Component
from dagster_components.core.context import ComponentLoadContext
from dagster_components.lib.definitions_component.scaffolder import DefinitionsComponentScaffolder
from dagster_components.resolved.model import ResolvableModel
from dagster_components.scaffold.scaffold import scaffold_with


@scaffold_with(DefinitionsComponentScaffolder)
class DefinitionsComponent(Component, ResolvableModel):
    """Wraps an arbitrary set of Dagster definitions."""

    definitions_path: Optional[str] = Field(
        None, description="Relative path to a file containing Dagster definitions."
    )

    def _build_defs_for_path(self, context: ComponentLoadContext, defs_path: Path) -> Definitions:
        defs_module = context.load_defs_relative_python_module(defs_path)
        defs_attrs = list(find_objects_in_module_of_types(defs_module, Definitions))

        if defs_attrs and self.definitions_path is None:
            raise ValueError(
                f"Found a Definitions object in {defs_path}, which is not supported when implicitly loading definitions. "
                "You may need to add an explicit `component.yaml` file to specify a DefinitionsComponent."
            )
        elif len(defs_attrs) > 1:
            raise ValueError(
                f"Found multiple Definitions objects in {defs_path}. At most one Definitions object "
                "may be specified when using the DefinitionsComponent."
            )
        elif len(defs_attrs) == 1:
            return defs_attrs[0]
        else:
            return load_definitions_from_module(defs_module)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        defs_paths = (
            [Path(self.definitions_path)]
            if self.definitions_path
            else list(context.path.rglob("*.py"))
        )

        return Definitions.merge(
            *(self._build_defs_for_path(context, defs_path) for defs_path in defs_paths)
        )
