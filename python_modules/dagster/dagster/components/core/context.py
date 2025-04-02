import contextlib
import contextvars
import dataclasses
import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Union

from dagster_shared.yaml_utils.source_position import SourcePositionTree

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster._utils import pushd
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils import get_path_from_module


@dataclass
class ComponentLoadContext:
    """Context for loading a single component."""

    path: Path
    defs_module_path: Path
    defs_module_name: str
    resolution_context: ResolutionContext

    @staticmethod
    def current() -> "ComponentLoadContext":
        context = active_component_load_context.get()
        if context is None:
            raise DagsterError(
                "No active component load context, `ComponentLoadContext.current()` must be called inside of a component's `build_defs` method"
            )
        return context

    @staticmethod
    def for_module(defs_module: ModuleType) -> "ComponentLoadContext":
        path = get_path_from_module(defs_module)
        return ComponentLoadContext(
            path=path,
            defs_module_path=path,
            defs_module_name=defs_module.__name__,
            resolution_context=ResolutionContext.default(),
        )

    @staticmethod
    def for_test() -> "ComponentLoadContext":
        return ComponentLoadContext(
            path=Path.cwd(),
            defs_module_path=Path.cwd(),
            defs_module_name="test",
            resolution_context=ResolutionContext.default(),
        )

    def _with_resolution_context(
        self, resolution_context: ResolutionContext
    ) -> "ComponentLoadContext":
        return dataclasses.replace(self, resolution_context=resolution_context)

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "ComponentLoadContext":
        return self._with_resolution_context(self.resolution_context.with_scope(**rendering_scope))

    def with_source_position_tree(
        self, source_position_tree: SourcePositionTree
    ) -> "ComponentLoadContext":
        return self._with_resolution_context(
            self.resolution_context.with_source_position_tree(source_position_tree)
        )

    def for_path(self, path: Path) -> "ComponentLoadContext":
        return dataclasses.replace(self, path=path)

    def defs_relative_module_name(self, path: Path) -> str:
        """Returns the name of the python module at the given path, relative to the project root."""
        container_path = self.path.parent if self.path.is_file() else self.path
        with pushd(str(container_path)):
            relative_path = path.resolve().relative_to(self.defs_module_path.resolve())
            if path.name == "__init__.py":
                # e.g. "a_project/defs/something/__init__.py" -> "a_project.defs.something"
                relative_parts = relative_path.parts[:-1]
            elif path.is_file():
                # e.g. "a_project/defs/something/file.py" -> "a_project.defs.something.file"
                relative_parts = [*relative_path.parts[:-1], relative_path.stem]
            else:
                # e.g. "a_project/defs/something/" -> "a_project.defs.something"
                relative_parts = relative_path.parts
            return ".".join([self.defs_module_name, *relative_parts])

    def normalize_component_type_str(self, type_str: str) -> str:
        return (
            f"{self.defs_relative_module_name(self.path)}{type_str}"
            if type_str.startswith(".")
            else type_str
        )

    def load_defs(self, module: ModuleType) -> Definitions:
        """Builds the set of Dagster definitions for a component module.

        This is useful for resolving dependencies on other components.
        """
        # FIXME: This should go through the component loader system
        # to allow for this value to be cached and more selectively
        # loaded. This is just a temporary hack to keep tests passing.
        from dagster.components.core.load_defs import load_defs

        return load_defs(module)

    def load_defs_relative_python_module(self, path: Path) -> ModuleType:
        """Load a python module relative to the defs's context path. This is useful for loading code
        the resides within the defs directory.

        Example:
            .. code-block:: python

                def build_defs(self, context: ComponentLoadContext) -> Definitions:
                    return load_definitions_from_module(
                        context.load_defs_relative_python_module(
                            Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
                        )
                    )

        In a typical setup you end up with module names such as "a_project.defs.my_component.my_python_file".

        This handles "__init__.py" files by ending the module name at the parent directory
        (e.g "a_project.defs.my_component") if the file resides at "a_project/defs/my_component/__init__.py".

        This calls importlib.import_module with that module name, going through the python module import system.

        It is as if one typed "import a_project.defs.my_component.my_python_file" in the python interpreter.
        """
        return importlib.import_module(self.defs_relative_module_name(path))


active_component_load_context: contextvars.ContextVar[Union[ComponentLoadContext, None]] = (
    contextvars.ContextVar("active_component_load_context", default=None)
)


@contextlib.contextmanager
def use_component_load_context(component_load_context: ComponentLoadContext):
    token = active_component_load_context.set(component_load_context)
    try:
        yield
    finally:
        active_component_load_context.reset(token)
