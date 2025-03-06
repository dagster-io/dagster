import contextlib
import contextvars
import dataclasses
import importlib
import importlib.metadata
import inspect
import sys
import textwrap
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional, TypedDict, TypeVar, Union

from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster._utils import pushd
from dagster._utils.cached_method import cached_method
from typing_extensions import Self

from dagster_components.core.component_key import ComponentKey
from dagster_components.core.component_scaffolder import DefaultComponentScaffolder
from dagster_components.core.schema.base import ResolvableSchema, resolve_as
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.scaffoldable.decorator import get_scaffolder, scaffoldable
from dagster_components.scaffoldable.scaffolder import ScaffolderUnavailableReason
from dagster_components.utils import format_error_message


class ComponentsEntryPointLoadError(DagsterError):
    pass


class ComponentDeclNode(ABC):
    @abstractmethod
    def load(self, context: "ComponentLoadContext") -> Sequence["Component"]: ...


@scaffoldable(scaffolder=DefaultComponentScaffolder)
class Component(ABC):
    @classmethod
    def get_schema(cls) -> Optional[type[ResolvableSchema]]:
        return None

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> Definitions: ...

    @classmethod
    def load(cls, attributes: Optional[ResolvableSchema], context: "ComponentLoadContext") -> Self:
        return resolve_as(attributes, cls, context.resolution_context) if attributes else cls()

    @classmethod
    def get_metadata(cls) -> "ComponentTypeInternalMetadata":
        docstring = cls.__doc__
        clean_docstring = _clean_docstring(docstring) if docstring else None

        scaffolder = get_scaffolder(cls)

        if isinstance(scaffolder, ScaffolderUnavailableReason):
            raise DagsterError(
                f"Component {cls.__name__} is not scaffoldable: {scaffolder.message}"
            )

        component_schema = cls.get_schema()
        scaffold_params = scaffolder.get_params()
        return {
            "summary": clean_docstring.split("\n\n")[0] if clean_docstring else None,
            "description": clean_docstring if clean_docstring else None,
            "scaffold_params_schema": None
            if scaffold_params is None
            else scaffold_params.model_json_schema(),
            "component_schema": None
            if component_schema is None
            else component_schema.model_json_schema(),
        }

    @classmethod
    def get_description(cls) -> Optional[str]:
        return inspect.getdoc(cls)


def _clean_docstring(docstring: str) -> str:
    lines = docstring.strip().splitlines()
    first_line = lines[0]
    if len(lines) == 1:
        return first_line
    else:
        rest = textwrap.dedent("\n".join(lines[1:]))
        return f"{first_line}\n{rest}"


class ComponentTypeInternalMetadata(TypedDict):
    summary: Optional[str]
    description: Optional[str]
    scaffold_params_schema: Optional[Any]  # json schema
    component_schema: Optional[Any]  # json schema


class ComponentTypeMetadata(ComponentTypeInternalMetadata):
    name: str
    namespace: str


def get_entry_points_from_python_environment(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


COMPONENTS_ENTRY_POINT_GROUP = "dagster.components"


def load_component_type(component_key: ComponentKey) -> type[Component]:
    module_name, attr = component_key.namespace, component_key.name
    try:
        module = importlib.import_module(module_name)
        if not hasattr(module, attr):
            raise DagsterError(f"Module `{module_name}` has no attribute `{attr}`.")
        component_type = getattr(module, attr)
        if not issubclass(component_type, Component):
            raise DagsterError(
                f"Attribute `{attr}` in module `{module_name}` is not a subclass of `dagster_components.Component`."
            )
        return component_type
    except ModuleNotFoundError as e:
        raise DagsterError(f"Module `{module_name}` not found.") from e
    except ImportError as e:
        raise DagsterError(f"Error loading module `{module_name}`.") from e


def discover_entry_point_component_types() -> dict[ComponentKey, type[Component]]:
    """Discover component types registered in the Python environment via the
    `dagster_components` entry point group.

    `dagster-components` itself registers multiple component entry points. We call these
    "builtin" component libraries. The `dagster_components` entry point resolves to published
    component types and is loaded by default. Other entry points resolve to various sets of test
    component types. This method will only ever load one builtin component library.
    """
    component_types: dict[ComponentKey, type[Component]] = {}
    entry_points = get_entry_points_from_python_environment(COMPONENTS_ENTRY_POINT_GROUP)

    for entry_point in entry_points:
        try:
            root_module = entry_point.load()
        except Exception as e:
            raise ComponentsEntryPointLoadError(
                format_error_message(f"""
                    Error loading entry point `{entry_point.name}` in group `{COMPONENTS_ENTRY_POINT_GROUP}`.
                    Please fix the error or uninstall the package that defines this entry point.
                """)
            ) from e

        if not isinstance(root_module, ModuleType):
            raise DagsterError(
                f"Invalid entry point {entry_point.name} in group {COMPONENTS_ENTRY_POINT_GROUP}. "
                f"Value expected to be a module, got {root_module}."
            )
        for name, component_type in get_component_types_in_module(root_module):
            key = ComponentKey(name=name, namespace=entry_point.value)
            component_types[key] = component_type
    return component_types


def discover_component_types(modules: Sequence[str]) -> dict[ComponentKey, type[Component]]:
    component_types: dict[ComponentKey, type[Component]] = {}
    for extra_module in modules:
        for name, component_type in get_component_types_in_module(
            importlib.import_module(extra_module)
        ):
            key = ComponentKey(name=name, namespace=extra_module)
            component_types[key] = component_type
    return component_types


def get_component_types_in_module(
    module: ModuleType,
) -> Iterable[tuple[str, type[Component]]]:
    for attr in dir(module):
        value = getattr(module, attr)
        if (
            isinstance(value, type)
            and issubclass(value, Component)
            and not inspect.isabstract(value)
        ):
            yield attr, value


T = TypeVar("T")


@dataclass
class DefinitionsModuleCache:
    """Cache used when loading a code location's component hierarchy.
    Stores resources and a cache to ensure we don't load the same component multiple times.
    """

    resources: Mapping[str, object]

    def build_defs_from_component_module(self, module: ModuleType) -> Definitions:
        """Loads a set of Dagster definitions from a components Python module.

        Args:
            module (ModuleType): The Python module to load definitions from.

        Returns:
            Definitions: The set of Dagster definitions loaded from the module.
        """
        return self._build_defs_from_component_module_inner(module)

    @cached_method
    def _build_defs_from_component_module_inner(self, module: ModuleType) -> Definitions:
        from dagster_components.core.component_decl_builder import module_to_decl_node
        from dagster_components.core.component_defs_builder import defs_from_components

        decl_node = module_to_decl_node(module)
        if not decl_node:
            raise Exception(f"No component found at module {module}")

        context = ComponentLoadContext(
            module_name=module.__name__,
            decl_node=decl_node,
            resolution_context=ResolutionContext.default(),
            module_cache=self,
        )
        with use_component_load_context(context):
            components = decl_node.load(context)
            return defs_from_components(
                resources=self.resources, context=context, components=components
            )


@dataclass
class ComponentLoadContext:
    """Context for loading a single component."""

    module_name: str
    decl_node: Optional[ComponentDeclNode]
    resolution_context: ResolutionContext
    module_cache: DefinitionsModuleCache

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
        decl_node: Optional[ComponentDeclNode] = None,
    ) -> "ComponentLoadContext":
        return ComponentLoadContext(
            module_name="test",
            decl_node=decl_node,
            resolution_context=ResolutionContext.default(),
            module_cache=DefinitionsModuleCache(resources=resources or {}),
        )

    @property
    def path(self) -> Path:
        from dagster_components.core.component_decl_builder import (
            PythonComponentDecl,
            YamlComponentDecl,
        )

        if not isinstance(self.decl_node, (YamlComponentDecl, PythonComponentDecl)):
            check.failed(f"Unsupported decl_node type {type(self.decl_node)}")

        return self.decl_node.path

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "ComponentLoadContext":
        return dataclasses.replace(
            self,
            resolution_context=self.resolution_context.with_scope(**rendering_scope),
        )

    def for_decl_node(self, decl_node: ComponentDeclNode) -> "ComponentLoadContext":
        return dataclasses.replace(self, decl_node=decl_node)

    def resolve(self, value: ResolvableSchema, as_type: type[T]) -> T:
        return self.resolution_context.resolve_value(value, as_type=as_type)

    def normalize_component_type_str(self, type_str: str) -> str:
        return f"{self.module_name}{type_str}" if type_str.startswith(".") else type_str

    def build_defs_from_component_module(self, module: ModuleType) -> Definitions:
        """Builds the set of Dagster definitions for a component module.

        This is useful for resolving dependencies on other components.
        """
        return self.module_cache.build_defs_from_component_module(module)

    def load_component_relative_python_module(self, file_path: Path) -> ModuleType:
        """Load a python module relative to the component's context path. This is useful for loading code
        the resides within the component directory, loaded during `build_defs` method of a component.

        Example:
            .. code-block:: python

                def build_defs(self, context: ComponentLoadContext) -> Definitions:
                    return load_definitions_from_module(
                        context.load_component_relative_python_module(
                            Path(self.definitions_path) if self.definitions_path else Path("definitions.py")
                        )
                    )

        In a typical setup you end up with module names such as "a_project.components.my_component.my_python_file".

        This handles "__init__.py" files by ending the module name at the parent directory
        (e.g "a_project.components.my_component") if the file resides at "a_project/defs/my_component/__init__.py".

        This calls importlib.import_module with that module name, going through the python module import system.

        It is as if one typed "import a_project.components.my_component.my_python_file" in the python interpreter.
        """
        abs_file_path = file_path.absolute()
        with pushd(str(self.path)):
            abs_context_path = self.path.absolute()

            # Problematic
            # See https://linear.app/dagster-labs/issue/BUILD-736/highly-suspect-hardcoding-of-components-string-is-component-relative
            component_module_relative_path = abs_context_path.parts[
                abs_context_path.parts.index("defs") + 2 :
            ]
            component_module_name = ".".join([self.module_name, *component_module_relative_path])
            if abs_file_path.name != "__init__.py":
                component_module_name = f"{component_module_name}.{abs_file_path.stem}"

            return importlib.import_module(component_module_name)


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


COMPONENT_LOADER_FN_ATTR = "__dagster_component_loader_fn"


T_Component = TypeVar("T_Component", bound=Component)


def component(
    fn: Callable[[ComponentLoadContext], T_Component],
) -> Callable[[ComponentLoadContext], T_Component]:
    setattr(fn, COMPONENT_LOADER_FN_ATTR, True)
    return fn


def is_component_loader(obj: Any) -> bool:
    return getattr(obj, COMPONENT_LOADER_FN_ATTR, False)
