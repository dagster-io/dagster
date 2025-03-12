from collections.abc import Sequence
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
from dagster_components.scaffold import scaffold_with


@scaffold_with(DefinitionsComponentScaffolder)
class DefinitionsComponent(Component, ResolvableModel):
    """Wraps an arbitrary set of Dagster definitions."""

    definitions_path: Optional[str] = Field(
        None, description="Relative path to a file containing Dagster definitions."
    )

    def _build_defs_for_paths(
        self, context: ComponentLoadContext, defs_paths: Sequence[Path]
    ) -> Definitions:
        explicit_defs: dict[Path, Definitions] = {}
        loaded_defs: dict[Path, Definitions] = {}
        for defs_path in defs_paths:
            defs_module = context.load_relative_python_module(defs_path)
            defs_attrs = list(find_objects_in_module_of_types(defs_module, Definitions))

            if len(defs_attrs) > 1:
                raise ValueError(
                    f"Found multiple Definitions objects in {defs_path}. At most one Definitions object "
                    "may be specified when using the DefinitionsComponent."
                )
            elif len(defs_attrs) == 1:
                explicit_defs[defs_path] = defs_attrs[0]
            else:
                loaded_defs[defs_path] = load_definitions_from_module(defs_module)

        if len(explicit_defs) > 1:
            raise ValueError(
                f"Found multiple files ({', '.join(path.name for path in explicit_defs)}) with explicit Definitions objects. "
                "At most one Definitions object may be defined in a given directory. This error can occur if you have a file "
                "named `definitions.py` in the same directory as other files defining `Definitions` objects."
            )
        elif len(explicit_defs) == 1:
            return next(iter(explicit_defs.values()))
        else:
            return Definitions.merge(*loaded_defs.values())

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        path = Path(self.definitions_path) if self.definitions_path else context.path
        defs_paths = list(path.rglob("*.py")) if path.is_dir() else [path]
        return self._build_defs_for_paths(context, defs_paths)
