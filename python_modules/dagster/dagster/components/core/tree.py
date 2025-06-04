import importlib
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Optional

from dagster_shared.record import record
from typing_extensions import TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.component_node import ComponentNode, DefsFolderComponentNode
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import DefsFolderComponent

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

TComponent = TypeVar("TComponent", bound=Component)


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

    @cached_property
    def root_node(self) -> DefsFolderComponentNode:
        return DefsFolderComponentNode.get(self.load_context)

    @cached_property
    def root(self) -> DefsFolderComponent:
        return self.root_node.load_component(self.load_context)

    def load_defs(self) -> Definitions:
        from dagster.components.core.load_defs import get_library_json_enriched_defs

        return Definitions.merge(
            self.root.build_defs(self.load_context),
            get_library_json_enriched_defs(self),
        )

    def _component_node_at_path(self, defs_path: Path) -> Optional[tuple[Path, ComponentNode]]:
        if self.root_node.path.absolute().as_posix() == defs_path.absolute().as_posix():
            return (self.root_node.path, self.root_node)
        for cp, component_node in self.root_node.iterate_path_component_node_pairs():
            defs_path_abs = (
                defs_path
                if defs_path.is_absolute()
                else (self.root_node.path / defs_path).absolute()
            )
            if cp.file_path.absolute().as_posix() == defs_path_abs.as_posix():
                return (cp.file_path, component_node)
        return None

    def load_defs_at_path(self, defs_path: Path) -> Definitions:
        """Loads definitions from the given defs subdirectory. Currently
        does not incorporate postprocessing from parent defs modules.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Definitions: The definitions loaded from the given path.
        """
        # impl to be fleshed out to flexibly handle different path types (str, list[str], ...)
        component_node_and_path = self._component_node_at_path(defs_path)
        if component_node_and_path:
            path, component_node = component_node_and_path
            ctx = self.load_context.for_path(path)
            return component_node.load_component(ctx).build_defs(ctx)

        raise Exception(f"No component found for path {defs_path}")

    def get_all_components(
        self,
        of_type: type[TComponent],
    ) -> list[TComponent]:
        """Get all components from this context that are instance of the specified type."""
        return [
            component
            for component in self.root.iterate_components()
            if isinstance(component, of_type)
        ]
