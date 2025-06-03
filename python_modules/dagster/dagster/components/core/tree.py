import importlib
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Optional

from dagster_shared.record import record
from typing_extensions import TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.cached_method import cached_method
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.decl import ComponentDecl, DefsFolderDecl
from dagster.components.core.defs_module import ComponentPath, DefsFolderComponent

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

TComponent = TypeVar("TComponent", bound=Component)


def _get_canonical_path_string(root_path: Path, path: Path) -> str:
    """Returns a canonical string representation of the given path (the absolute, POSIX path)
    to use for e.g. dict keys or path comparisons.
    """
    return (root_path / path if not path.is_absolute() else path).absolute().as_posix()


@record(
    checked=False,  # cant handle ModuleType
)
class ComponentTree:
    defs_module: ModuleType
    project_root: Path

    @staticmethod
    def load(path_within_project: Path) -> "ComponentTree":
        """Using the provided path, find the nearest parent python project and load the
        ComponentTree using its configuration.
        """
        from dagster_dg_core.context import DgContext

        # replace with dagster_shared impl of path crawl and config resolution
        dg_context = DgContext.for_project_environment(path_within_project, command_line_config={})

        return ComponentTree(
            defs_module=importlib.import_module(dg_context.defs_module_name),
            project_root=dg_context.root_path,
        )

    @cached_property
    def load_context(self):
        return ComponentLoadContext.for_module(
            defs_module=self.defs_module, project_root=self.project_root
        )

    @cached_method
    def find_root_decl(self) -> DefsFolderDecl:
        return DefsFolderDecl.get(self.load_context)

    @cached_method
    def load_root_component(self) -> DefsFolderComponent:
        return self.find_root_decl()._load_component()  # noqa: SLF001

    @cached_method
    def build_defs(self) -> Definitions:
        from dagster.components.core.load_defs import get_library_json_enriched_defs

        return Definitions.merge(
            self.load_root_component().build_defs(self.load_context),
            get_library_json_enriched_defs(self),
        )

    @cached_method
    def _component_decl_tree(self) -> Sequence[tuple[ComponentPath, ComponentDecl]]:
        """Constructs or returns the full component declaration tree from cache."""
        tree = list(self.find_root_decl().iterate_path_component_decl_pairs())
        return tree

    @cached_method
    def _component_decl_at_posix_path(
        self, defs_path_posix: str
    ) -> Optional[tuple[Path, ComponentDecl]]:
        """Locates a component declaration matching the given canonical string path."""
        root_decl = self.find_root_decl()
        if root_decl.path.absolute().as_posix() == defs_path_posix:
            return (root_decl.path, root_decl)
        for cp, component_decl in self._component_decl_tree():
            if cp.file_path.absolute().as_posix() == defs_path_posix:
                return (cp.file_path, component_decl)
        return None

    @cached_method
    def _component_at_posix_path(self, defs_path_posix: str) -> Optional[tuple[Path, Component]]:
        component_decl_and_path = self._component_decl_at_posix_path(defs_path_posix)
        if component_decl_and_path:
            path, component_decl = component_decl_and_path
            return (path, component_decl._load_component())  # noqa: SLF001
        return None

    @cached_method
    def _defs_at_posix_path(self, defs_path_posix: str) -> Optional[Definitions]:
        component = self._component_at_posix_path(defs_path_posix)
        if component is None:
            return None
        path, component = component
        return component.build_defs(self.load_context.for_path(path))

    def find_decl_at_path(self, defs_path: Path) -> ComponentDecl:
        """Loads a component declaration from the given path.

        Args:
            defs_path: Path to the component declaration to load. If relative, resolves relative to the defs root.

        Returns:
            ComponentDecl: The component declaration loaded from the given path.
        """
        component_decl_and_path = self._component_decl_at_posix_path(
            _get_canonical_path_string(self.find_root_decl().path, defs_path)
        )
        if component_decl_and_path is None:
            raise Exception(f"No component decl found for path {defs_path}")
        return component_decl_and_path[1]

    def load_component_at_path(self, defs_path: Path) -> Component:
        """Loads a component from the given path.

        Args:
            defs_path: Path to the component to load. If relative, resolves relative to the defs root.

        Returns:
            Component: The component loaded from the given path.
        """
        component = self._component_at_posix_path(
            _get_canonical_path_string(self.find_root_decl().path, defs_path)
        )
        if component is None:
            raise Exception(f"No component found for path {defs_path}")
        path, component = component
        return component

    def build_defs_at_path(self, defs_path: Path) -> Definitions:
        """Builds definitions from the given defs subdirectory. Currently
        does not incorporate postprocessing from parent defs modules.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Definitions: The definitions loaded from the given path.
        """
        defs = self._defs_at_posix_path(
            _get_canonical_path_string(self.find_root_decl().path, defs_path)
        )
        if defs is None:
            raise Exception(f"No definitions found for path {defs_path}")
        return defs

    def get_all_components(
        self,
        of_type: type[TComponent],
    ) -> list[TComponent]:
        """Get all components from this context that are instance of the specified type."""
        return [
            component
            for component in self.load_root_component().iterate_components()
            if isinstance(component, of_type)
        ]
