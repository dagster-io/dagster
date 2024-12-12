import copy
import importlib
import importlib.metadata
import sys
from abc import ABC, abstractmethod
from types import ModuleType
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Iterable, Mapping, Optional, Sequence, Type

from dagster import _check as check
from dagster._core.errors import DagsterError
from dagster._utils import snakecase
from typing_extensions import Self

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class ComponentDeclNode: ...


class Component(ABC):
    name: ClassVar[Optional[str]] = None
    component_params_schema: ClassVar = None
    generate_params_schema: ClassVar = None

    @classmethod
    def generate_files(cls, params: Any) -> Optional[Mapping[str, Any]]: ...

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...

    @classmethod
    @abstractmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self: ...


def get_entry_points_from_python_environment(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


COMPONENTS_ENTRY_POINT_GROUP = "dagster.components"


class ComponentRegistry:
    @classmethod
    def from_entry_point_discovery(cls) -> "ComponentRegistry":
        components: Dict[str, Type[Component]] = {}
        for entry_point in get_entry_points_from_python_environment(COMPONENTS_ENTRY_POINT_GROUP):
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
