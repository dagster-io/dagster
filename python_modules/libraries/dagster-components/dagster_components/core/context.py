import contextlib
import contextvars
import dataclasses
import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Optional, Union

from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster._utils import pushd

from dagster_components.resolved.context import ResolutionContext

if TYPE_CHECKING:
    from dagster_components.core.defs_module import DefsModuleDecl
    from dagster_components.core.load_defs import DefinitionsModuleCache


@dataclass
class ComponentLoadContext:
    """Context for loading a single component."""

    defs_root: Path
    defs_module_name: str
    decl_node: Optional["DefsModuleDecl"]
    resolution_context: ResolutionContext
    module_cache: "DefinitionsModuleCache"

    @staticmethod
    def current() -> "ComponentLoadContext":
        context = active_component_load_context.get()
        if context is None:
            raise DagsterError(
                "No active component load context, `ComponentLoadContext.current()` must be called inside of a component's `build_defs` method"
            )
        return context

    @staticmethod
    def for_test(
        *,
        resources: Optional[Mapping[str, object]] = None,
        decl_node: Optional["DefsModuleDecl"] = None,
    ) -> "ComponentLoadContext":
        from dagster_components.core.load_defs import DefinitionsModuleCache

        return ComponentLoadContext(
            defs_root=Path.cwd(),
            defs_module_name="test",
            decl_node=decl_node,
            resolution_context=ResolutionContext.default(),
            module_cache=DefinitionsModuleCache(resources=resources or {}),
        )

    @property
    def path(self) -> Path:
        return check.not_none(self.decl_node).path

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "ComponentLoadContext":
        return dataclasses.replace(
            self,
            resolution_context=self.resolution_context.with_scope(**rendering_scope),
        )

    def for_decl(self, decl: "DefsModuleDecl") -> "ComponentLoadContext":
        return dataclasses.replace(self, decl_node=decl)

    def defs_relative_module_name(self, path: Path) -> str:
        """Returns the name of the python module at the given path, relative to the project root."""
        container_path = self.path.parent if self.path.is_file() else self.path
        with pushd(str(container_path)):
            relative_path = path.resolve().relative_to(self.defs_root.resolve())
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
        return self.module_cache.load_defs(module)

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
