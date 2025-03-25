from collections.abc import Sequence
from pathlib import Path
from typing import Any

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_module,
)
from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._record import record

from dagster_components.core.context import ComponentLoadContext
from dagster_components.core.defs_module.defs_builder import DefsBuilder


@record
class DefsModule(DefsBuilder):
    path: Path


@record
class SubpackageDefsModule(DefsModule):
    """A folder containing multiple submodules."""

    submodules: Sequence[DefsModule]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions.merge(*(submodule.build_defs(context) for submodule in self.submodules))


@record
class PythonDefsModule(DefsModule):
    """A module containing python dagster definitions."""

    module: Any  # ModuleType

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        definitions_objects = list(find_objects_in_module_of_types(self.module, Definitions))
        if len(definitions_objects) == 0:
            return load_definitions_from_module(self.module)
        elif len(definitions_objects) == 1:
            return next(iter(definitions_objects))
        else:
            raise DagsterInvalidDefinitionError(
                f"Found multiple Definitions objects in {self.path}. At most one Definitions object "
                "may be specified per module."
            )


@record
class BuilderDefsModule(DefsModule):
    """A module containing a DefsBuilder."""

    inner: DefsBuilder

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return self.inner.build_defs(context)
