import copy
from abc import ABC, abstractmethod
from types import ModuleType
from typing import TYPE_CHECKING, ClassVar, Dict, Iterable, Mapping, Optional, Type

from dagster._core.errors import DagsterError
from dagster._utils import snakecase
from typing_extensions import Self

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class ComponentDeclNode: ...


class Component(ABC):
    name: ClassVar[Optional[str]] = None

    @classmethod
    def registered_name(cls) -> str:
        return cls.name or snakecase(cls.__name__)

    @classmethod
    def generate_files(cls) -> None:
        raise NotImplementedError()

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...

    @classmethod
    @abstractmethod
    def from_decl_node(
        cls, context: "ComponentLoadContext", decl_node: "ComponentDeclNode"
    ) -> Self: ...


class ComponentRegistry:
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


def register_components_in_module(registry: ComponentRegistry, root_module: ModuleType) -> None:
    from dagster._core.definitions.load_assets_from_modules import (
        find_modules_in_package,
        find_subclasses_in_module,
    )

    for module in find_modules_in_package(root_module):
        for component in find_subclasses_in_module(module, (Component,)):
            if component is Component:
                continue
            registry.register(component.registered_name(), component)


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
