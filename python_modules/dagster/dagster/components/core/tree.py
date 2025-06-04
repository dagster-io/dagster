import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Optional, Union

from typing_extensions import TypeVar

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.cached_method import cached_method
from dagster.components.component.component import Component
from dagster.components.core.component_node import ComponentNode, DefsFolderComponentNode
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import DefsFolderComponent

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

TComponent = TypeVar("TComponent", bound=Component)


@dataclass
class ComponentTree:
    defs_module: ModuleType
    project_root: Path
    terminate_autoloading_on_keyword_files: Optional[bool] = None

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
            defs_module=self.defs_module,
            project_root=self.project_root,
            component_tree=self,
            **(
                {}
                if self.terminate_autoloading_on_keyword_files is None
                else {
                    "terminate_autoloading_on_keyword_files": self.terminate_autoloading_on_keyword_files
                }
            ),
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

    def _component_node_at_path(
        self, abs_defs_path_posix: str
    ) -> Optional[tuple[Path, ComponentNode]]:
        if self.root_node.path.absolute().as_posix() == abs_defs_path_posix:
            return (self.root_node.path, self.root_node)
        for cp, component_node in self.root_node.iterate_path_component_node_pairs():
            if cp.file_path.absolute().as_posix() == abs_defs_path_posix:
                return (cp.file_path, component_node)
        return None

    def load_defs_at_path(self, defs_path: Union[Path, str]) -> Definitions:
        """Loads definitions from the given defs subdirectory. Currently
        does not incorporate postprocessing from parent defs modules.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Definitions: The definitions loaded from the given path.
        """
        defs_path_obj = Path(defs_path)
        defs_path_abs = (
            defs_path_obj
            if defs_path_obj.is_absolute()
            else (self.load_context.defs_module_path / defs_path_obj).absolute()
        )
        return self._load_defs_at_path_inner(defs_path_abs.as_posix())

    @cached_method
    def _load_defs_at_path_inner(self, abs_defs_path_posix: str) -> Definitions:
        # impl to be fleshed out to flexibly handle different path types (str, list[str], ...)
        component_node_and_path = self._component_node_at_path(abs_defs_path_posix)
        if component_node_and_path:
            path, component_node = component_node_and_path
            ctx = self.load_context.for_path(path)
            return component_node.load_component(ctx).build_defs(ctx)

        raise Exception(f"No component found for path {abs_defs_path_posix}")

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

    def get_all_asset_keys_at_path(self, defs_path: Union[Path, str]) -> Sequence[AssetKey]:
        """Get all asset keys from the given defs subdirectory.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Sequence[AssetKey]: The set of asset keys from the given path.
        """
        defs = self.load_defs_at_path(defs_path)
        specs = defs.get_all_asset_specs()
        return [spec.key for spec in specs]
