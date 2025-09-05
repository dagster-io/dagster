import importlib
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional, Union, overload
from unittest import mock

from dagster_shared import check
from dagster_shared.record import IHaveNew, record
from dagster_shared.utils.config import (
    discover_config_file,
    get_canonical_defs_module_name,
    load_toml_as_dict,
)
from typing_extensions import Self, TypeVar

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster.components.component.component import Component
from dagster.components.core.component_tree_state import ComponentTreeStateTracker
from dagster.components.core.context import ComponentDeclLoadContext, ComponentLoadContext
from dagster.components.core.decl import (
    ComponentDecl,
    ComponentLoaderDecl,
    PythonFileDecl,
    YamlDecl,
    build_component_decl_from_context,
)
from dagster.components.core.defs_module import (
    ComponentPath,
    CompositeYamlComponent,
    DefsFolderComponent,
    PythonFileComponent,
    ResolvableToComponentPath,
)
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils import get_path_from_module

PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY = "plugin_component_types_json"

T = TypeVar("T", bound=Component)
TComponent = TypeVar("TComponent", bound=Component)


@record
class ComponentWithContext:
    component: Component
    component_decl: ComponentDecl


class ComponentTreeException(Exception):
    pass


@record(
    checked=False,  # cant handle ModuleType
)
class ComponentTree(IHaveNew):
    """The hierarchy of Component instances defined in the project.

    Manages and caches the component loading process, including finding component declarations
    to build the initial declaration tree, loading these Components, and eventually building the
    Definitions.
    """

    defs_module: ModuleType
    project_root: Path
    terminate_autoloading_on_keyword_files: Optional[bool] = None

    @cached_property
    def state_tracker(self) -> ComponentTreeStateTracker:
        return ComponentTreeStateTracker(self.defs_module_path)

    @contextmanager
    def augment_component_tree_exception(
        self, path: ResolvableToComponentPath, msg_for_path: Callable[[str], str]
    ):
        try:
            yield
        except Exception as e:
            resolved_path = ComponentPath.from_resolvable(self.defs_module_path, path)
            if not isinstance(e, ComponentTreeException):
                raise ComponentTreeException(
                    f"{msg_for_path(resolved_path.get_relative_key(self.defs_module_path))}:\n{self.to_string_representation(include_load_and_build_status=True, match_path=resolved_path)}"
                ) from e
            raise

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
    def for_project(cls, path_within_project: Path) -> Self:
        """Using the provided path, find the nearest parent python project and load the
        ComponentTree using its configuration.

        Args:
            path_within_project (Path): A path within a Dagster project.

        Returns:
            ComponentTree: The ComponentTree for the project.
        """
        root_config_path = discover_config_file(path_within_project)
        if not root_config_path:
            raise DagsterError(
                f"Could not find config file (pyproject.toml/dg.toml) in {path_within_project} or any parent of."
            )

        toml_config = load_toml_as_dict(root_config_path)

        if root_config_path and root_config_path.stem == "dg":
            project = toml_config.get("project", {})
        else:
            project = toml_config.get("tool", {}).get("dg", {}).get("project", {})

        root_module_name = project.get("root_module")
        defs_module_name = project.get("defs_module")
        check.invariant(
            defs_module_name or root_module_name,
            f"Either defs_module or root_module must be set in the project config {root_config_path}",
        )
        defs_module_name = get_canonical_defs_module_name(defs_module_name, root_module_name)

        defs_module = importlib.import_module(defs_module_name)

        return cls(
            defs_module=defs_module,
            project_root=root_config_path.parent,
        )

    @property
    def decl_load_context(self) -> ComponentDeclLoadContext:
        if self.state_tracker.get_cache_data(self.defs_module_path).decl_load_context is None:
            self.state_tracker.set_cache_data(
                self.defs_module_path,
                decl_load_context=ComponentDeclLoadContext(
                    component_path=ComponentPath.from_path(self.defs_module_path),
                    project_root=self.project_root,
                    defs_module_path=self.defs_module_path,
                    defs_module_name=self.defs_module_name,
                    resolution_context=ResolutionContext.default(),
                    terminate_autoloading_on_keyword_files=False,
                    component_tree=self,
                ),
            )
        return check.not_none(
            self.state_tracker.get_cache_data(self.defs_module_path).decl_load_context
        )

    @property
    def load_context(self) -> ComponentLoadContext:
        if self.state_tracker.get_cache_data(self.defs_module_path).load_context is None:
            self.state_tracker.set_cache_data(
                self.defs_module_path,
                load_context=ComponentLoadContext.from_decl_load_context(
                    self.decl_load_context, self.find_root_decl()
                ),
            )
        return check.not_none(self.state_tracker.get_cache_data(self.defs_module_path).load_context)

    def load_root_component(self) -> Component:
        return self.load_structural_component_at_path(self.defs_module_path)

    def find_root_decl(self) -> ComponentDecl:
        if self.state_tracker.get_cache_data(self.defs_module_path).component_decl is None:
            self.state_tracker.set_cache_data(
                self.defs_module_path,
                component_decl=build_component_decl_from_context(self.decl_load_context),
            )
        return check.not_none(
            self.state_tracker.get_cache_data(self.defs_module_path).component_decl
        )

    def build_defs(self) -> Definitions:
        from dagster.components.core.load_defs import get_library_json_enriched_defs

        if self.state_tracker.get_cache_data(self.defs_module_path).defs is None:
            defs = Definitions.merge(
                self.build_defs_at_path(self.defs_module_path),
                get_library_json_enriched_defs(self),
            )
            self.state_tracker.set_cache_data(self.defs_module_path, defs=defs)

        return check.not_none(self.state_tracker.get_cache_data(self.defs_module_path).defs)

    def find_decl_at_path(self, defs_path: ResolvableToComponentPath) -> ComponentDecl:
        """Loads a component declaration from the given path.

        Args:
            defs_path: Path to the component declaration to load. If relative, resolves relative to the defs root.

        Returns:
            ComponentDecl: The component declaration loaded from the given path.
        """
        resolved_path = ComponentPath.from_resolvable(self.defs_module_path, defs_path)
        decl = self._component_decl_tree().get(resolved_path)
        if decl is None:
            raise Exception(f"No component decl found for path {defs_path}")
        return decl

    def mark_component_load_dependency(
        self, from_path: ComponentPath, to_path: ComponentPath
    ) -> None:
        """Marks a dependency between the component at `from_path` and the component at `to_path`.

        Args:
            from_path: The path to the component that depends on the component at `to_path`.
            to_path: The path to the component that the component at `from_path` depends on.
        """
        self.state_tracker.mark_component_load_dependency(from_path, to_path)

    def mark_component_defs_dependency(
        self, from_path: ComponentPath, to_path: ComponentPath
    ) -> None:
        """Marks a dependency between the component at `from_path` on the defs of
        the component at `to_path`.

        Args:
            from_path: The path to the component that depends on the defs of the component at `to_path`.
            to_path: The path to the component that the component at `from_path` depends on.
        """
        self.state_tracker.mark_component_defs_dependency(from_path, to_path)

    def mark_component_defs_state_key(
        self, component_path: ComponentPath, defs_state_key: str
    ) -> None:
        """Marks a defs state key for the component at `component_path`.

        Args:
            component_path: The path to the component to mark the state key for.
            defs_state_key: The state key to mark.
        """
        self.state_tracker.mark_component_defs_state_key(component_path, defs_state_key)

    @overload
    def load_component_at_path(self, defs_path: Union[Path, ComponentPath, str]) -> Component: ...
    @overload
    def load_component_at_path(
        self, defs_path: Union[Path, ComponentPath, str], expected_type: type[T]
    ) -> T: ...

    def load_component_at_path(
        self, defs_path: Union[Path, ComponentPath, str], expected_type: Optional[type[T]] = None
    ) -> Any:
        """Loads a component from the given path.

        Args:
            defs_path: Path to the component to load. If relative, resolves relative to the defs root.

        Returns:
            Component: The component loaded from the given path.
        """
        component = self.load_structural_component_at_path(defs_path)
        if (
            isinstance(component, (CompositeYamlComponent, PythonFileComponent))
            and len(component.components) == 1
        ):
            component = (
                component.components[0]
                if isinstance(component, CompositeYamlComponent)
                else next(iter(component.components.values()))
            )
        if expected_type and not isinstance(component, expected_type):
            raise Exception(f"Component at path {defs_path} is not of type {expected_type}")

        return component

    def _component_decl_tree(self) -> dict[ComponentPath, ComponentDecl]:
        """Constructs or returns the full component declaration tree from cache."""
        root_decl = self.find_root_decl()
        return dict(root_decl.iterate_path_component_decl_pairs())

    def _component_and_context_at_path(
        self, defs_path: ResolvableToComponentPath
    ) -> Optional[tuple[Component, ComponentDecl]]:
        if self.state_tracker.get_cache_data(defs_path).component is None:
            with self.augment_component_tree_exception(
                defs_path,
                lambda path: f"Error while loading component {path}",
            ):
                resolved_path = ComponentPath.from_resolvable(self.defs_module_path, defs_path)
                component_decl = self._component_decl_tree().get(resolved_path)
                if component_decl:
                    self.state_tracker.set_cache_data(
                        defs_path,
                        component=component_decl._load_component(),  # noqa: SLF001
                        component_decl=component_decl,
                    )
        cache_data = self.state_tracker.get_cache_data(defs_path)
        if cache_data.component is None or cache_data.component_decl is None:
            return None
        return (cache_data.component, cache_data.component_decl)

    def _build_defs_at_path(self, defs_path: ResolvableToComponentPath) -> Optional[Definitions]:
        cached_data = self.state_tracker.get_cache_data(defs_path)
        if cached_data.defs:
            return cached_data.defs

        with self.augment_component_tree_exception(
            defs_path,
            lambda path: f"Error while building definitions for {path}",
        ):
            component_info = self._component_and_context_at_path(defs_path)
            if component_info is None:
                raise Exception(f"No component found for path {defs_path}")

            component, component_decl = component_info
            clc = ComponentLoadContext.from_decl_load_context(
                component_decl.context, component_decl
            )

            defs = component.build_defs(clc)
            self.state_tracker.set_cache_data(defs_path, defs=defs)
            return defs

    def load_structural_component_at_path(self, defs_path: ResolvableToComponentPath) -> Component:
        """Loads a component from the given path, does not resolve e.g. CompositeYamlComponent to an underlying
        component type.

        Args:
            defs_path: Path to the component to load. If relative, resolves relative to the defs root.

        Returns:
            Component: The component loaded from the given path.
        """
        component_with_context = self._component_and_context_at_path(defs_path)
        if component_with_context is None:
            raise Exception(f"No component found for path {defs_path}")
        return component_with_context[0]

    def build_defs_at_path(self, defs_path: ResolvableToComponentPath) -> Definitions:
        """Builds definitions from the given defs subdirectory. Currently
        does not incorporate postprocessing from parent defs modules.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Definitions: The definitions loaded from the given path.
        """
        defs = self._build_defs_at_path(defs_path)
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

    def _has_loaded_component_at_path(self, path: ResolvableToComponentPath) -> bool:
        resolved_path = ComponentPath.from_resolvable(self.defs_module_path, path)
        return self.state_tracker.get_cache_data(resolved_path).component is not None

    def _has_built_defs_at_path(self, path: Union[Path, ComponentPath]) -> bool:
        resolved_path = ComponentPath.from_resolvable(self.defs_module_path, path)
        return self.state_tracker.get_cache_data(resolved_path).defs is not None

    def is_fully_loaded(self) -> bool:
        return self._has_loaded_component_at_path(self.defs_module_path)

    def has_built_all_defs(self) -> bool:
        return self._has_built_defs_at_path(self.defs_module_path)

    def _add_string_representation(
        self,
        lines: list[str],
        decl: ComponentDecl,
        prefix: str,
        include_load_and_build_status: bool = False,
        hide_plain_defs: bool = False,
        match_path: Optional[ComponentPath] = None,
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
                name = str(child_decl.path.instance_key)
            elif isinstance(child_decl, YamlDecl):
                file_path = file_path / "defs.yaml"
                component_type = child_decl.component_cls.__name__

                if child_decl.path.instance_key is not None and len(decls) > 1:
                    name = f"{file_path}[{child_decl.path.instance_key}]"
                else:
                    name = str(file_path)
            else:
                name = str(file_path)

            connector = "└── " if idx == total - 1 else "├── "
            out_txt = f"{prefix}{connector}{name}"

            if component_type:
                out_txt += f" ({component_type})"

            is_error = (
                match_path
                and child_decl.path.file_path.as_posix() == match_path.file_path.as_posix()
                and child_decl.path.instance_key == match_path.instance_key
            )
            if include_load_and_build_status:
                if is_error:
                    out_txt = f"{out_txt} (error)"
                elif self._has_built_defs_at_path(child_decl.path):
                    out_txt = f"{out_txt} (built)"
                elif self._has_loaded_component_at_path(child_decl.path):
                    out_txt = f"{out_txt} (loaded)"

            lines.append(out_txt)

            if is_error:
                lines.append(f"{prefix}{' ' * len(connector)}{'^' * len(name)}")

            extension = "    " if idx == total - 1 else "│   "
            self._add_string_representation(
                lines,
                child_decl,
                prefix + extension,
                include_load_and_build_status,
                hide_plain_defs,
                match_path,
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
        self,
        include_load_and_build_status: bool = False,
        hide_plain_defs: bool = False,
        match_path: Optional[ComponentPath] = None,
    ) -> str:
        """Returns a string representation of the component tree.

        Args:
            include_load_and_build_status: Whether to include the load and build status of the components.
            hide_plain_defs: Whether to hide any plain Dagster defs, which are not components, e.g. Python files without components.
        """
        lines = []
        self._add_string_representation(
            lines,
            self.find_root_decl(),
            "",
            include_load_and_build_status,
            hide_plain_defs,
            match_path,
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

    @property
    def decl_load_context(self):
        return ComponentDeclLoadContext(
            component_path=ComponentPath.from_path(self.defs_module_path),
            project_root=self.project_root,
            defs_module_path=self.defs_module_path,
            defs_module_name=self.defs_module_name,
            resolution_context=ResolutionContext.default(),
            terminate_autoloading_on_keyword_files=True,
            component_tree=self,
        )

    @property
    def load_context(self):
        component_decl = mock.Mock()
        component_decl.iterate_child_component_decls = mock.Mock(return_value=[])
        return ComponentLoadContext.from_decl_load_context(self.decl_load_context, component_decl)


class LegacyAutoloadingComponentTree(ComponentTree):
    """ComponentTree variant which terminates autoloading of defs on the keyword
    files `definitions.py` and `component.py`. This should only be used for legacy
    test and load_defs codepaths.
    """

    @property
    def decl_load_context(self):
        return ComponentDeclLoadContext(
            component_path=ComponentPath.from_path(self.defs_module_path),
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
