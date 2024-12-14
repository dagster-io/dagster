import copy
import importlib
import importlib.metadata
import inspect
import sys
import textwrap
from abc import ABC, abstractmethod
from pathlib import Path
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypedDict,
)

from dagster import _check as check
from dagster._core.errors import DagsterError
from dagster._record import record
from dagster._utils import snakecase
from typing_extensions import Self

from dagster_components.utils import ensure_dagster_components_tests_import

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class ComponentDeclNode: ...


@record
class ComponentGenerateRequest:
    component_type_name: str
    component_instance_root_path: Path


class Component(ABC):
    name: ClassVar[Optional[str]] = None
    params_schema: ClassVar = None
    generate_params_schema: ClassVar = None

    @classmethod
    def generate_files(cls, request: ComponentGenerateRequest, params: Any) -> None: ...

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...

    @classmethod
    @abstractmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self: ...

    @classmethod
    def get_metadata(cls) -> "ComponentInternalMetadata":
        docstring = cls.__doc__
        clean_docstring = _clean_docstring(docstring) if docstring else None

        return {
            "summary": clean_docstring.split("\n\n")[0] if clean_docstring else None,
            "description": clean_docstring if clean_docstring else None,
            "generate_params_schema": cls.generate_params_schema.schema()
            if cls.generate_params_schema
            else None,
            "component_params_schema": cls.params_schema.schema() if cls.params_schema else None,
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


class ComponentInternalMetadata(TypedDict):
    summary: Optional[str]
    description: Optional[str]
    generate_params_schema: Optional[Any]  # json schema
    component_params_schema: Optional[Any]  # json schema


class ComponentMetadata(ComponentInternalMetadata):
    name: str
    package: str


def get_entry_points_from_python_environment(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


COMPONENTS_ENTRY_POINT_GROUP = "dagster.components"
BUILTIN_COMPONENTS_ENTRY_POINT_BASE = "dagster_components"
BUILTIN_PUBLISHED_COMPONENT_ENTRY_POINT = BUILTIN_COMPONENTS_ENTRY_POINT_BASE
BUILTIN_TEST_COMPONENT_ENTRY_POINT = ".".join([BUILTIN_COMPONENTS_ENTRY_POINT_BASE, "test"])


class ComponentRegistry:
    @classmethod
    def from_entry_point_discovery(
        cls, builtin_component_lib: str = BUILTIN_PUBLISHED_COMPONENT_ENTRY_POINT
    ) -> "ComponentRegistry":
        """Discover components registered in the Python environment via the `dagster_components` entry point group.

        `dagster-components` itself registers multiple component entry points. We call these
        "builtin" component libraries. The `dagster_components` entry point resolves to published
        components and is loaded by default. Other entry points resolve to various sets of test
        components. This method will only ever load one builtin component library.

        Args:
            builtin-component-lib (str): Specifies the builtin components library to load. Builtin
            copmonents libraries are defined under entry points with names matching the pattern
            `dagster_components*`. Only one builtin component library can be loaded at a time.
            Defaults to `dagster_components`, the standard set of published components.
        """
        components: Dict[str, Type[Component]] = {}
        for entry_point in get_entry_points_from_python_environment(COMPONENTS_ENTRY_POINT_GROUP):
            # Skip builtin entry points that are not the specified builtin component library.
            if (
                entry_point.name.startswith(BUILTIN_COMPONENTS_ENTRY_POINT_BASE)
                and not entry_point.name == builtin_component_lib
            ):
                continue
            elif entry_point.name == BUILTIN_TEST_COMPONENT_ENTRY_POINT:
                if builtin_component_lib:
                    ensure_dagster_components_tests_import()
                else:
                    continue

            root_module = entry_point.load()
            if not isinstance(root_module, ModuleType):
                raise DagsterError(
                    f"Invalid entry point {entry_point.name} in group {COMPONENTS_ENTRY_POINT_GROUP}. "
                    f"Value expected to be a module, got {root_module}."
                )
            for component in get_registered_components_in_module(root_module):
                key = f"{entry_point.name}.{get_component_name(component)}"
                components[key] = component

        return cls(components)

    def __init__(self, components: Dict[str, Type[Component]]):
        self._components: Dict[str, Type[Component]] = copy.copy(components)

    @staticmethod
    def empty() -> "ComponentRegistry":
        return ComponentRegistry({})

    def register(self, name: str, component: Type[Component]) -> None:
        if name in self._components:
            raise DagsterError(f"There is an existing component registered under {name}")
        self._components[name] = component

    def has(self, name: str) -> bool:
        return name in self._components

    def get(self, name: str) -> Type[Component]:
        return self._components[name]

    def keys(self) -> Iterable[str]:
        return self._components.keys()

    def __repr__(self) -> str:
        return f"<ComponentRegistry {list(self._components.keys())}>"


def get_registered_components_in_module(module: ModuleType) -> Iterable[Type[Component]]:
    from dagster._core.definitions.load_assets_from_modules import find_subclasses_in_module

    for component in find_subclasses_in_module(module, (Component,)):
        if is_registered_component(component):
            yield component


class ComponentLoadContext:
    def __init__(self, *, resources: Mapping[str, object], registry: ComponentRegistry):
        self.registry = registry
        self.resources = resources

    @staticmethod
    def for_test(
        *,
        resources: Optional[Mapping[str, object]] = None,
        registry: Optional[ComponentRegistry] = None,
    ) -> "ComponentLoadContext":
        return ComponentLoadContext(
            resources=resources or {}, registry=registry or ComponentRegistry.empty()
        )


COMPONENT_REGISTRY_KEY_ATTR = "__dagster_component_registry_key"


def component(
    cls: Optional[Type[Component]] = None,
    *,
    name: Optional[str] = None,
) -> Any:
    if cls is None:

        def wrapper(actual_cls: Type[Component]) -> Type[Component]:
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


def is_registered_component(cls: Type) -> bool:
    return hasattr(cls, COMPONENT_REGISTRY_KEY_ATTR)


def get_component_name(component_type: Type[Component]) -> str:
    check.param_invariant(
        is_registered_component(component_type),
        "component_type",
        "Expected a registered component. Use @component to register a component.",
    )
    return getattr(component_type, COMPONENT_REGISTRY_KEY_ATTR)
