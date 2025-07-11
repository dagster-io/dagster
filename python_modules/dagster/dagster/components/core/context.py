import dataclasses
import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Union

from dagster_shared import check
from dagster_shared.yaml_utils.source_position import SourcePositionTree
from typing_extensions import Self

from dagster._annotations import PublicAttr, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import pushd
from dagster.components.resolved.context import ResolutionContext

if TYPE_CHECKING:
    from dagster.components.component.component import Component
    from dagster.components.core.decl import ComponentDecl
    from dagster.components.core.defs_module import ComponentPath
    from dagster.components.core.tree import ComponentTree


RESOLUTION_CONTEXT_STASH_KEY = "component_load_context"


@public
@dataclass(frozen=True)
class ComponentDeclLoadContext:
    """Context object that provides environment and path information during loading of
    ComponentDecls. This context is automatically created and passed to ComponentDecl
    objects when loading a project's defs folder. Each Python module or folder in the
    defs directory receives a unique context instance that provides access to project
    structure, paths, and utilities.

    Args:
        path: The filesystem path of the component decl currently being loaded.
            For a file: ``/path/to/project/src/project/defs/my_component.py``
            For a directory: ``/path/to/project/src/project/defs/my_component/``
        project_root: The root directory of the Dagster project, typically containing
            ``pyproject.toml`` or ``setup.py``. Example: ``/path/to/project``
        defs_module_path: The filesystem path to the root defs folder.
            Example: ``/path/to/project/src/project/defs``
        defs_module_name: The Python module name for the root defs folder, used for
            import resolution. Typically follows the pattern ``"project_name.defs"``.
            Example: ``"my_project.defs"``
        resolution_context: The resolution context used by the component templating
            system for parameter resolution and variable substitution.
        component_tree: The component tree that contains the component decl currently being loaded.
        terminate_autoloading_on_keyword_files: Controls whether autoloading stops
            when encountering ``definitions.py`` or ``component.py`` files.
            **Deprecated**: This parameter will be removed after version 1.11.

                )

    Note:
        This context is automatically provided by Dagster's autoloading system and
        should not be instantiated manually in most cases. For testing purposes,
        use ``ComponentTree.for_test().decl_load_context`` to create a test instance.

    See Also:
        - :py:func:`dagster.definitions`: Decorator that receives this context
        - :py:class:`dagster.Definitions`: The object typically returned by context-using functions
        - :py:class:`dagster.components.resolved.context.ResolutionContext`: Underlying resolution context
        - :py:class:`dagster.ComponentLoadContext`: Context available when instantiating Components
    """

    path: PublicAttr[Path]
    project_root: PublicAttr[Path]
    defs_module_path: PublicAttr[Path]
    defs_module_name: PublicAttr[str]
    resolution_context: PublicAttr[ResolutionContext]
    component_tree: "ComponentTree"
    terminate_autoloading_on_keyword_files: bool

    def __post_init__(self):
        object.__setattr__(
            self,
            "resolution_context",
            self.resolution_context.with_stashed_value(RESOLUTION_CONTEXT_STASH_KEY, self),
        )

    @staticmethod
    def from_resolution_context(
        resolution_context: ResolutionContext,
    ) -> "ComponentDeclLoadContext":
        return check.inst(
            resolution_context.stash.get(RESOLUTION_CONTEXT_STASH_KEY), ComponentDeclLoadContext
        )

    def _with_resolution_context(self, resolution_context: ResolutionContext) -> "Self":
        return dataclasses.replace(self, resolution_context=resolution_context)

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "Self":
        return self._with_resolution_context(
            self.resolution_context.with_scope(
                **rendering_scope,
                **{
                    "project_root": str(self.project_root.resolve()),
                },
            )
        )

    def with_source_position_tree(self, source_position_tree: SourcePositionTree) -> "Self":
        return self._with_resolution_context(
            self.resolution_context.with_source_position_tree(source_position_tree)
        )

    def for_path(self, path: Path) -> "Self":
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

    def load_structural_component_at_path(
        self, defs_path: Union[Path, "ComponentPath"]
    ) -> "Component":
        """Loads a component from the given path.

        Args:
            defs_path: Path to the component to load. If relative, resolves relative to the defs root.

        Returns:
            Component: The component loaded from the given path.
        """
        return self.component_tree.load_structural_component_at_path(defs_path)


@public
@dataclass(frozen=True)
class ComponentLoadContext(ComponentDeclLoadContext):
    """Context object that provides environment and path information during component loading.
    This context is automatically created and passed to component definitions when loading
    a project's defs folder. Each Python module or folder in the defs directory receives
    a unique context instance that provides access to the underlying ComponentDecl,
    project structure, paths, and utilities for dynamic component instantiation.

    The context enables components to:
    - Access project and module path information
    - Load other modules and definitions within the project
    - Resolve relative imports and module names
    - Access templating and resolution capabilities

    Args:
        path: The filesystem path of the component currently being loaded.
            For a file: ``/path/to/project/src/project/defs/my_component.py``
            For a directory: ``/path/to/project/src/project/defs/my_component/``
        project_root: The root directory of the Dagster project, typically containing
            ``pyproject.toml`` or ``setup.py``. Example: ``/path/to/project``
        defs_module_path: The filesystem path to the root defs folder.
            Example: ``/path/to/project/src/project/defs``
        defs_module_name: The Python module name for the root defs folder, used for
            import resolution. Typically follows the pattern ``"project_name.defs"``.
            Example: ``"my_project.defs"``
        resolution_context: The resolution context used by the component templating
            system for parameter resolution and variable substitution.
        component_tree: The component tree that contains the component currently being loaded.
        terminate_autoloading_on_keyword_files: Controls whether autoloading stops
            when encountering ``definitions.py`` or ``component.py`` files.
            **Deprecated**: This parameter will be removed after version 1.11.
        component_decl: The associated ComponentDecl to the component being loaded.

    Note:
        This context is automatically provided by Dagster's autoloading system and
        should not be instantiated manually in most cases. For testing purposes,
        use ``ComponentTree.for_test().load_context`` to create a test instance.

    See Also:
        - :py:func:`dagster.definitions`: Decorator that receives this context
        - :py:class:`dagster.Definitions`: The object typically returned by context-using functions
        - :py:class:`dagster.components.resolved.context.ResolutionContext`: Underlying resolution context
        - :py:class:`dagster.ComponentDeclLoadContext`: Context available when loading ComponentDecls
    """

    component_decl: "ComponentDecl"

    @staticmethod
    def from_decl_load_context(
        decl_load_context: ComponentDeclLoadContext,
        component_decl: "ComponentDecl",
    ) -> "ComponentLoadContext":
        """Augments a ComponentDeclLoadContext with the ComponentDecl being loaded.

        Args:
            decl_load_context: The ComponentDeclLoadContext to augment.
            component_decl: The ComponentDecl being loaded.

        Returns:
            ComponentLoadContext: An augmented context which can be used to
            load and build definitions for the component.
        """
        return ComponentLoadContext(
            path=decl_load_context.path,
            project_root=decl_load_context.project_root,
            defs_module_path=decl_load_context.defs_module_path,
            defs_module_name=decl_load_context.defs_module_name,
            resolution_context=decl_load_context.resolution_context,
            component_tree=decl_load_context.component_tree,
            terminate_autoloading_on_keyword_files=decl_load_context.terminate_autoloading_on_keyword_files,
            component_decl=component_decl,
        )

    def build_defs_at_path(self, defs_path: Union[Path, "ComponentPath"]) -> Definitions:
        """Builds definitions from the given defs subdirectory. Currently
        does not incorporate postprocessing from parent defs modules.

        Args:
            defs_path: Path to the defs module to load. If relative, resolves relative to the defs root.

        Returns:
            Definitions: The definitions loaded from the given path.
        """
        return self.component_tree.build_defs_at_path(defs_path)
