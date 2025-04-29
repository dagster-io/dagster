import contextlib
import contextvars
import dataclasses
import importlib
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Optional, Union

from dagster_shared.yaml_utils.source_position import SourcePositionTree

from dagster._annotations import PublicAttr, preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster._utils import pushd
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils import get_path_from_module

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.components_storage.types import ComponentChange


class YamlComponentStorage(ABC):
    @abstractmethod
    def is_in_storage(self, context: "ComponentLoadContext") -> bool: ...

    @abstractmethod
    def read_declaration(self, context: "ComponentLoadContext") -> str: ...

    def subcontexts(self, context: "ComponentLoadContext") -> Iterable["ComponentLoadContext"]:
        for subpath in context.path.iterdir():
            yield context.for_path(subpath)


class LocalYamlComponentStorage(YamlComponentStorage):
    def is_in_storage(self, context: "ComponentLoadContext") -> bool:
        return (context.path / "component.yaml").exists()

    def read_declaration(self, context: "ComponentLoadContext") -> str:
        return (context.path / "component.yaml").read_text()


@public
@preview(emit_runtime_warning=False)
@dataclass
class ComponentLoadContext:
    """Context for loading a single component."""

    path: PublicAttr[Path]
    project_root: PublicAttr[Path]
    defs_module_path: PublicAttr[Path]
    defs_module_name: PublicAttr[str]
    resolution_context: PublicAttr[ResolutionContext]
    yaml_component_storage: PublicAttr[YamlComponentStorage]

    @staticmethod
    def current() -> "ComponentLoadContext":
        context = active_component_load_context.get()
        if context is None:
            raise DagsterError(
                "No active component load context, `ComponentLoadContext.current()` must be called inside of a component's `build_defs` method"
            )
        return context

    @staticmethod
    def for_module(defs_module: ModuleType, project_root: Path) -> "ComponentLoadContext":
        path = get_path_from_module(defs_module)
        return ComponentLoadContext(
            path=path,
            project_root=project_root,
            defs_module_path=path,
            defs_module_name=defs_module.__name__,
            resolution_context=ResolutionContext.default(),
            yaml_component_storage=LocalYamlComponentStorage(),
        )

    @property
    def component_key(self) -> str:
        return str(self.path.resolve().relative_to(self.defs_module_path.resolve()))

    def path_from_component_key(self, component_key: str) -> Path:
        """Returns the absolute path for a given component key."""
        return self.defs_module_path.resolve() / component_key

    def for_preview(
        self,
        component_key: str,
        preview_changes: list["ComponentChange"],
        instance: "DagsterInstance",
    ) -> "ComponentLoadContext":
        from dagster.components.preview.yaml_storage import PreviewYamlComponentStorage

        return dataclasses.replace(
            self,
            path=self.path_from_component_key(component_key),
            yaml_component_storage=PreviewYamlComponentStorage(preview_changes, instance),
        )

    @staticmethod
    def for_test(
        *,
        path: Optional[Path] = None,
        yaml_component_storage: Optional[YamlComponentStorage] = None,
    ) -> "ComponentLoadContext":
        return ComponentLoadContext(
            path=path if path else Path.cwd(),
            project_root=Path.cwd(),
            defs_module_path=Path.cwd(),
            defs_module_name="test",
            resolution_context=ResolutionContext.default(),
            yaml_component_storage=yaml_component_storage
            if yaml_component_storage
            else LocalYamlComponentStorage(),
        )

    def _with_resolution_context(
        self, resolution_context: ResolutionContext
    ) -> "ComponentLoadContext":
        return dataclasses.replace(self, resolution_context=resolution_context)

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "ComponentLoadContext":
        return self._with_resolution_context(
            self.resolution_context.with_scope(
                **rendering_scope,
                **{
                    "project_root": str(self.project_root.resolve()),
                },
            )
        )

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

        return load_defs(module, self.project_root)

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
