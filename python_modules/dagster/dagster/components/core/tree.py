import importlib
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Optional, Union
from unittest import mock

from dagster_shared import check
from dagster_shared.record import record
from dagster_shared.utils.cached_method import get_cached_method_cache, make_cached_method_cache_key
from typing_extensions import Self, TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.cached_method import cached_method
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentDeclLoadContext, ComponentLoadContext
from dagster.components.core.decl import (
    ComponentDecl,
    ComponentLoaderDecl,
    PythonFileDecl,
    YamlDecl,
    build_component_decl_from_context,
)
from dagster.components.core.defs_module import ComponentPath, DefsFolderComponent
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils import get_path_from_module

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

TComponent = TypeVar("TComponent", bound=Component)


def _get_canonical_path_string(root_path: Path, path: Path) -> str:
    """Returns a canonical string representation of the given path (the absolute, POSIX path)
    to use for e.g. dict keys or path comparisons.
    """
    return (root_path / path if not path.is_absolute() else path).absolute().as_posix()


def _get_canonical_component_path(
    root_path: Path, path: Union[Path, ComponentPath]
) -> tuple[str, Optional[Union[int, str]]]:
    if isinstance(path, ComponentPath):
        return _get_canonical_path_string(root_path, path.file_path), path.instance_key
    return _get_canonical_path_string(root_path, path), None


@record
class ComponentWithContext:
    path: Path
    component: Component
    component_decl: ComponentDecl


@record(
    checked=False,  # cant handle ModuleType
)
class ComponentTree:
    """Manages and caches the component loading process, including finding component decls
    to build the initial decl tree, loading these components, and eventually building the
    defs.
    """

    defs_module: ModuleType
    project_root: Path

    @property
    def defs_module_name(self) -> str:
        return self.defs_module.__name__

    @property
    def defs_module_path(self) -> Path:
        return get_path_from_module(self.defs_module)

    @staticmethod
    def for_test() -> "ComponentTree":
        return TestComponentTree.for_test()

    @staticmethod
    def from_module(
        defs_module: ModuleType,
        project_root: Path,
    ) -> "ComponentTree":
        """Convenience method for creating a ComponentTree from a module.

        Args:
            defs_module: The defs module of the project, typically the `defs` directory.
            project_root: The root of the project.
            terminate_autoloading_on_keyword_files: Whether to terminate autoloading on keyword files such as
                `definitions.py` or `component.py`.

        Returns:
            A ComponentTree.
        """
        return ComponentTree(
            defs_module=defs_module,
            project_root=project_root,
        )

    @classmethod
    def load(cls, path_within_project: Path) -> Self:
        """Using the provided path, find the nearest parent python project and load the
        ComponentTree using its configuration.
        """
        from dagster_dg_core.context import DgContext

        # replace with dagster_shared impl of path crawl and config resolution
        dg_context = DgContext.for_project_environment(path_within_project, command_line_config={})

        defs_module = importlib.import_module(dg_context.defs_module_name)

        return cls(
            defs_module=defs_module,
            project_root=dg_context.root_path,
        )

    @cached_property
    def decl_load_context(self):
        return ComponentDeclLoadContext(
            path=self.defs_module_path,
            project_root=self.project_root,
            defs_module_path=self.defs_module_path,
            defs_module_name=self.defs_module_name,
            resolution_context=ResolutionContext.default(),
            terminate_autoloading_on_keyword_files=False,
            component_tree=self,
        )

    @cached_property
    def load_context(self):
        return ComponentLoadContext.from_decl_load_context(
            self.decl_load_context, self.find_root_decl()
        )

    @cached_method
    def find_root_decl(self) -> ComponentDecl:
        return check.not_none(build_component_decl_from_context(self.decl_load_context))

    @cached_method
    def load_root_component(self) -> Component:
        return self.load_component_at_path(self.defs_module_path)

    @cached_method
    def build_defs(self) -> Definitions:
        from dagster.components.core.load_defs import get_library_json_enriched_defs

        return Definitions.merge(
            self.build_defs_at_path(self.defs_module_path),
            get_library_json_enriched_defs(self),
        )

    @cached_method
    def _component_decl_tree(self) -> Sequence[tuple[ComponentPath, ComponentDecl]]:
        """Constructs or returns the full component declaration tree from cache."""
        root_decl = self.find_root_decl()
        return list(root_decl.iterate_path_component_decl_pairs())

    @cached_method
    def _component_decl_at_posix_path(
        self, defs_path_posix: str, instance_key: Optional[Union[int, str]]
    ) -> Optional[tuple[Path, ComponentDecl]]:
        """Locates a component declaration matching the given canonical string path."""
        for cp, component_decl in self._component_decl_tree():
            if (
                cp.file_path.absolute().as_posix() == defs_path_posix
                and cp.instance_key == instance_key
            ):
                return (cp.file_path, component_decl)
        return None

    @cached_method
    def _component_and_context_at_posix_path(
        self, defs_path_posix: str, instance_key: Optional[Union[int, str]]
    ) -> Optional[ComponentWithContext]:
        component_decl_and_path = self._component_decl_at_posix_path(defs_path_posix, instance_key)
        if component_decl_and_path:
            path, component_decl = component_decl_and_path
            return ComponentWithContext(
                path=path,
                component=component_decl._load_component(),  # noqa: SLF001
                component_decl=component_decl,
            )
        return None

    @cached_method
    def _defs_at_posix_path(
        self, defs_path_posix: str, instance_key: Optional[Union[int, str]]
    ) -> Optional[Definitions]:
        component_info = self._component_and_context_at_posix_path(defs_path_posix, instance_key)
        if component_info is None:
            return None
        component = component_info.component
        component_decl = component_info.component_decl

        clc = ComponentLoadContext.from_decl_load_context(component_decl.context, component_decl)
        return component.build_defs(clc)

    def find_decl_at_path(self, defs_path: Union[Path, ComponentPath]) -> ComponentDecl:
        """Loads a component declaration from the given path.

        Args:
            defs_path: Path to the component declaration to load. If relative, resolves relative to the defs root.

        Returns:
            ComponentDecl: The component declaration loaded from the given path.
        """
        component_decl_and_path = self._component_decl_at_posix_path(
            *_get_canonical_component_path(self.defs_module_path, defs_path)
        )
        if component_decl_and_path is None:
            raise Exception(f"No component decl found for path {defs_path}")
        return component_decl_and_path[1]

    def load_component_at_path(self, defs_path: Union[Path, ComponentPath]) -> Component:
        """Loads a component from the given path.

        Args:
            defs_path: Path to the component to load. If relative, resolves relative to the defs root.

        Returns:
            Component: The component loaded from the given path.
        """
        component = self._component_and_context_at_posix_path(
            *_get_canonical_component_path(self.defs_module_path, defs_path)
        )
        if component is None:
            raise Exception(f"No component found for path {defs_path}")
        return component.component

    def build_defs_at_path(self, defs_path: Union[Path, ComponentPath]) -> Definitions:
        """Builds definitions from the given defs subdirectory. Currently
        does not incorporate postprocessing from parent defs modules.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Definitions: The definitions loaded from the given path.
        """
        defs = self._defs_at_posix_path(
            *_get_canonical_component_path(self.defs_module_path, defs_path)
        )
        if defs is None:
            raise Exception(f"No definitions found for path {defs_path}")
        return defs

    def get_all_components(
        self,
        of_type: type[TComponent],
    ) -> list[TComponent]:
        """Get all components from this context that are instance of the specified type."""
        root_component = self.load_root_component()
        if not isinstance(root_component, DefsFolderComponent):
            raise Exception("Root component is not a DefsFolderComponent")
        return [
            component
            for component in root_component.iterate_components()
            if isinstance(component, of_type)
        ]

    def _has_loaded_component_at_path(self, path: Union[Path, ComponentPath]) -> bool:
        cache = get_cached_method_cache(self, "_component_and_context_at_posix_path")
        canonical_path = _get_canonical_component_path(self.defs_module_path, path)
        key = make_cached_method_cache_key(
            {"defs_path_posix": canonical_path[0], "instance_key": canonical_path[1]}
        )
        return key in cache

    def _has_built_defs_at_path(self, path: Union[Path, ComponentPath]) -> bool:
        cache = get_cached_method_cache(self, "_defs_at_posix_path")
        canonical_path = _get_canonical_component_path(self.defs_module_path, path)
        key = make_cached_method_cache_key(
            {"defs_path_posix": canonical_path[0], "instance_key": canonical_path[1]}
        )
        return key in cache

    def _add_string_representation(
        self,
        lines: list[str],
        decl: ComponentDecl,
        prefix: str,
        include_load_and_build_status: bool = False,
        hide_plain_defs: bool = False,
    ) -> None:
        decls = list(decl.iterate_child_component_decls())
        parent_path = decl.path.file_path

        total = len(decls)
        for idx, child_decl in enumerate(decls):
            if isinstance(child_decl, PythonFileDecl) and not child_decl.decls and hide_plain_defs:
                continue

            component_type = None
            file_path = child_decl.path.file_path.relative_to(parent_path)

            if isinstance(child_decl, ComponentLoaderDecl):
                name = child_decl.path.instance_key
                if child_decl.component_node_fn.__annotations__.get("return"):
                    component_type = child_decl.component_node_fn.__annotations__["return"].__name__
            elif isinstance(child_decl, YamlDecl):
                file_path = file_path / "defs.yaml"
                component_type = child_decl.component_cls.__name__

                if child_decl.path.instance_key is not None and len(decls) > 1:
                    name = f"{file_path}[{child_decl.path.instance_key}]"
                else:
                    name = file_path
            else:
                name = file_path

            connector = "└── " if idx == total - 1 else "├── "
            out_txt = f"{prefix}{connector}{name}"

            if component_type:
                out_txt += f" ({component_type})"

            if include_load_and_build_status:
                if self._has_built_defs_at_path(child_decl.path):
                    out_txt += " (built)"
                elif self._has_loaded_component_at_path(child_decl.path):
                    out_txt += " (loaded)"

            lines.append(out_txt)

            extension = "    " if idx == total - 1 else "│   "
            self._add_string_representation(
                lines,
                child_decl,
                prefix + extension,
                include_load_and_build_status,
                hide_plain_defs,
            )

        if (
            hide_plain_defs
            and len(decls) > 0
            and all(
                isinstance(child_decl, PythonFileDecl) and not child_decl.decls
                for child_decl in decls
            )
        ):
            lines.append(f"{prefix}└── ...")

    def to_string_representation(
        self, include_load_and_build_status: bool = False, hide_plain_defs: bool = False
    ) -> str:
        """Returns a string representation of the component tree.

        Args:
            include_load_and_build_status: Whether to include the load and build status of the components.
            hide_plain_defs: Whether to hide any plain Dagster defs, which are not components, e.g. Python files without components.
        """
        lines = []
        self._add_string_representation(
            lines, self.find_root_decl(), "", include_load_and_build_status, hide_plain_defs
        )
        return "\n".join(lines)


class TestComponentTree(ComponentTree):
    """Variant of ComponentTree that is used for testing purposes. Mocks out the
    definitions module name and path.
    """

    @staticmethod
    def for_test() -> "TestComponentTree":
        """Convenience method for creating a ComponentTree for testing purposes."""
        return TestComponentTree(
            defs_module=mock.Mock(),
            project_root=Path.cwd(),
        )

    @property
    def defs_module_name(self) -> str:
        return "test"

    @property
    def defs_module_path(self) -> Path:
        return Path.cwd()

    @cached_property
    def decl_load_context(self):
        return ComponentDeclLoadContext(
            path=self.defs_module_path,
            project_root=self.project_root,
            defs_module_path=self.defs_module_path,
            defs_module_name=self.defs_module_name,
            resolution_context=ResolutionContext.default(),
            terminate_autoloading_on_keyword_files=True,
            component_tree=self,
        )

    @cached_property
    def load_context(self):
        component_decl = mock.Mock()
        component_decl.iterate_child_component_decls = mock.Mock(return_value=[])
        return ComponentLoadContext.from_decl_load_context(self.decl_load_context, component_decl)


class LegacyAutoloadingComponentTree(ComponentTree):
    """ComponentTree variant which terminates autoloading of defs on the keyword
    files `definitions.py` and `component.py`. This should only be used for legacy
    test and load_defs codepaths.
    """

    @cached_property
    def decl_load_context(self):
        return ComponentDeclLoadContext(
            path=self.defs_module_path,
            project_root=self.project_root,
            defs_module_path=self.defs_module_path,
            defs_module_name=self.defs_module_name,
            resolution_context=ResolutionContext.default(),
            terminate_autoloading_on_keyword_files=True,
            component_tree=self,
        )

    @staticmethod
    def from_module(
        defs_module: ModuleType,
        project_root: Path,
    ) -> "ComponentTree":
        """Convenience method for creating a ComponentTree from a module.

        Args:
            defs_module: The defs module of the project, typically the `defs` directory.
            project_root: The root of the project.
            terminate_autoloading_on_keyword_files: Whether to terminate autoloading on keyword files such as
                `definitions.py` or `component.py`.

        Returns:
            A ComponentTree.
        """
        return LegacyAutoloadingComponentTree(
            defs_module=defs_module,
            project_root=project_root,
        )
