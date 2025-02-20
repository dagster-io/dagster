import copy
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
from dagster._utils import snakecase
from typing_extensions import Self

from dagster_components.core.component_key import (
    ComponentKey,
    GlobalComponentKey,
    LocalComponentKey,
)
from dagster_components.core.component_scaffolder import (
    ComponentScaffolder,
    ComponentScaffolderUnavailableReason,
    DefaultComponentScaffolder,
)
from dagster_components.core.schema.base import ResolvableSchema
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.utils import format_error_message, load_module_from_path


class ComponentsEntryPointLoadError(DagsterError):
    pass


class ComponentDeclNode(ABC):
    @abstractmethod
    def load(self, context: "ComponentLoadContext") -> Sequence["Component"]: ...


class Component(ABC):
    @classmethod
    def get_schema(cls) -> Optional[type[ResolvableSchema]]:
        return None

    @classmethod
    def get_scaffolder(cls) -> Union[ComponentScaffolder, ComponentScaffolderUnavailableReason]:
        """Subclasses should implement this method to override scaffolding behavior. If this component
        is not meant to be scaffolded it returns a ComponentScaffolderUnavailableReason with a message
        This can be determined at runtime based on the environment or configuration. For example,
        if scaffolders are optionally installed as extras (for example to avoid heavy dependencies in production),
        this method should return a ComponentScaffolderUnavailableReason with a message explaining
        how to install the necessary extras.
        """
        return DefaultComponentScaffolder()

    @classmethod
    def get_additional_scope(cls) -> Mapping[str, Any]:
        return {}

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> Definitions: ...

    @classmethod
    def load(cls, attributes: Optional[ResolvableSchema], context: "ComponentLoadContext") -> Self:
        return attributes.resolve_as(cls, context.resolution_context) if attributes else cls()

    @classmethod
    def get_metadata(cls) -> "ComponentTypeInternalMetadata":
        docstring = cls.__doc__
        clean_docstring = _clean_docstring(docstring) if docstring else None

        scaffolder = cls.get_scaffolder()

        if isinstance(scaffolder, ComponentScaffolderUnavailableReason):
            raise DagsterError(
                f"Component {cls.__name__} is not scaffoldable: {scaffolder.message}"
            )

        component_schema = cls.get_schema()
        scaffold_params = scaffolder.get_schema()
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
BUILTIN_COMPONENTS_ENTRY_POINT_BASE = "dagster_components"
BUILTIN_MAIN_COMPONENT_ENTRY_POINT = BUILTIN_COMPONENTS_ENTRY_POINT_BASE
BUILTIN_TEST_COMPONENT_ENTRY_POINT = ".".join([BUILTIN_COMPONENTS_ENTRY_POINT_BASE, "test"])


class ComponentTypeRegistry:
    @classmethod
    def from_entry_point_discovery(
        cls, builtin_component_lib: str = BUILTIN_MAIN_COMPONENT_ENTRY_POINT
    ) -> "ComponentTypeRegistry":
        """Discover component types registered in the Python environment via the
        `dagster_components` entry point group.

        `dagster-components` itself registers multiple component entry points. We call these
        "builtin" component libraries. The `dagster_components` entry point resolves to published
        component types and is loaded by default. Other entry points resolve to various sets of test
        component types. This method will only ever load one builtin component library.

        Args:
            builtin-component-lib (str): Specifies the builtin components library to load. Built-in
            component libraries are defined under entry points with names matching the pattern
            `dagster_components*`. Only one built-in  component library can be loaded at a time.
            Defaults to `dagster_components`, the standard set of published component types.
        """
        component_types: dict[ComponentKey, type[Component]] = {}
        for entry_point in get_entry_points_from_python_environment(COMPONENTS_ENTRY_POINT_GROUP):
            # Skip built-in entry points that are not the specified builtin component library.
            if (
                entry_point.name.startswith(BUILTIN_COMPONENTS_ENTRY_POINT_BASE)
                and not entry_point.name == builtin_component_lib
            ):
                continue

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
            for component_type in get_registered_component_types_in_module(root_module):
                key = GlobalComponentKey(
                    name=get_component_type_name(component_type), namespace=entry_point.name
                )
                component_types[key] = component_type

        return cls(component_types)

    def __init__(self, component_types: dict[ComponentKey, type[Component]]):
        self._component_types: dict[ComponentKey, type[Component]] = copy.copy(component_types)

    @staticmethod
    def empty() -> "ComponentTypeRegistry":
        return ComponentTypeRegistry({})

    def register(self, key: ComponentKey, component_type: type[Component]) -> None:
        if key in self._component_types:
            raise DagsterError(f"There is an existing component registered under {key}")
        self._component_types[key] = component_type

    def has(self, key: ComponentKey) -> bool:
        return key in self._component_types

    def get(self, key: ComponentKey) -> type[Component]:
        if isinstance(key, LocalComponentKey):
            for component_type in find_component_types_in_file(key.python_file):
                if get_component_type_name(component_type) == key.name:
                    return component_type
            raise ValueError(
                f"Could not find component type {key.to_typename()} in {key.python_file}"
            )
        else:
            return self._component_types[key]

    def keys(self) -> Iterable[ComponentKey]:
        return self._component_types.keys()

    def items(self) -> Iterable[tuple[ComponentKey, type[Component]]]:
        return self._component_types.items()

    def __repr__(self) -> str:
        return f"<ComponentRegistry {list(self._component_types.keys())}>"


def get_registered_component_types_in_module(module: ModuleType) -> Iterable[type[Component]]:
    from dagster._core.definitions.module_loaders.load_assets_from_modules import (
        find_subclasses_in_module,
    )

    for component in find_subclasses_in_module(module, (Component,)):
        if is_registered_component_type(component):
            yield component


T = TypeVar("T")


@dataclass
class ComponentLoadContext:
    module_name: str
    resources: Mapping[str, object]
    registry: ComponentTypeRegistry
    decl_node: Optional[ComponentDeclNode]
    resolution_context: ResolutionContext

    @staticmethod
    def for_test(
        *,
        resources: Optional[Mapping[str, object]] = None,
        registry: Optional[ComponentTypeRegistry] = None,
        decl_node: Optional[ComponentDeclNode] = None,
    ) -> "ComponentLoadContext":
        return ComponentLoadContext(
            module_name="test",
            resources=resources or {},
            registry=registry or ComponentTypeRegistry.empty(),
            decl_node=decl_node,
            resolution_context=ResolutionContext.default(),
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


COMPONENT_REGISTRY_KEY_ATTR = "__dagster_component_registry_key"
COMPONENT_LOADER_FN_ATTR = "__dagster_component_loader_fn"


def registered_component_type(
    cls: Optional[type[Component]] = None, *, name: Optional[str] = None
) -> Any:
    """Decorator for registering a component type. You must annotate a component
    type with this decorator in order for it to be inspectable and loaded by tools.

    Args:
        cls (Optional[Type[Component]]): The target of the decorator: the component class
            to register. The class must inherit from Component.
        name (Optional[str]): The name to register the component type under. If not
            provided, the name will be the snake-cased version of the class name. The
            name is used as a key in operations like scaffolding and loading.
    """
    if cls is None:

        def wrapper(actual_cls: type[Component]) -> type[Component]:
            check.inst_param(actual_cls, "actual_cls", type)
            setattr(
                actual_cls,
                COMPONENT_REGISTRY_KEY_ATTR,
                name or snakecase(actual_cls.__name__),
            )
            return actual_cls

        return wrapper
    else:
        # called without params
        check.inst_param(cls, "cls", type)
        setattr(cls, COMPONENT_REGISTRY_KEY_ATTR, name or snakecase(cls.__name__))
        return cls


def is_registered_component_type(cls: type) -> bool:
    return hasattr(cls, COMPONENT_REGISTRY_KEY_ATTR)


def get_component_type_name(component_type: type[Component]) -> str:
    check.param_invariant(
        is_registered_component_type(component_type),
        "component_type",
        "Expected a registered component. Use @component to register a component.",
    )
    return getattr(component_type, COMPONENT_REGISTRY_KEY_ATTR)


T_Component = TypeVar("T_Component", bound=Component)


def component(
    fn: Callable[[ComponentLoadContext], T_Component],
) -> Callable[[ComponentLoadContext], T_Component]:
    setattr(fn, COMPONENT_LOADER_FN_ATTR, True)
    return fn


def is_component_loader(obj: Any) -> bool:
    return getattr(obj, COMPONENT_LOADER_FN_ATTR, False)


def find_component_types_in_file(file_path: Path) -> list[type[Component]]:
    """Find all component types defined in a specific file."""
    component_types = []
    for _name, obj in inspect.getmembers(
        load_module_from_path(file_path.stem, file_path), inspect.isclass
    ):
        assert isinstance(obj, type)
        if is_registered_component_type(obj):
            component_types.append(obj)
    return component_types


def find_local_component_types(component_path: Path) -> Mapping[LocalComponentKey, type[Component]]:
    """Find all component types defined in a component directory, and their respective paths."""
    component_types = {}
    for py_file in component_path.glob("*.py"):
        for component_type in find_component_types_in_file(py_file):
            component_types[
                LocalComponentKey(
                    name=get_component_type_name(component_type),
                    namespace=f"file:{py_file.name}",
                    dirpath=py_file.parent,
                )
            ] = component_type
    return component_types
