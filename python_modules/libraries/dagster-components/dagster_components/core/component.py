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
from typing import Any, ClassVar, Optional, TypedDict, TypeVar, Union, cast

import click
from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster._utils import pushd, snakecase
from dagster._utils.pydantic_yaml import enrich_validation_errors_with_source_position
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self

from dagster_components.core.component_scaffolder import (
    ComponentScaffolder,
    ComponentScaffolderUnavailableReason,
    DefaultComponentScaffolder,
)
from dagster_components.core.schema.resolver import TemplatedValueResolver


class ComponentDeclNode: ...


class Component(ABC):
    name: ClassVar[Optional[str]] = None

    @classmethod
    def get_schema(cls) -> Optional[type[BaseModel]]:
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
    @abstractmethod
    def load(cls, context: "ComponentLoadContext") -> Self: ...

    @classmethod
    def get_metadata(cls) -> "ComponentTypeInternalMetadata":
        docstring = cls.__doc__
        clean_docstring = _clean_docstring(docstring) if docstring else None

        scaffolder = cls.get_scaffolder()

        if isinstance(scaffolder, ComponentScaffolderUnavailableReason):
            raise DagsterError(
                f"Component {cls.__name__} is not scaffoldable: {scaffolder.message}"
            )

        component_params = cls.get_schema()
        scaffold_params = scaffolder.get_params_schema_type()
        return {
            "summary": clean_docstring.split("\n\n")[0] if clean_docstring else None,
            "description": clean_docstring if clean_docstring else None,
            "scaffold_params_schema": None
            if scaffold_params is None
            else scaffold_params.model_json_schema(),
            "component_params_schema": None
            if component_params is None
            else component_params.model_json_schema(),
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


def _get_click_cli_help(command: click.Command) -> str:
    with click.Context(command) as ctx:
        formatter = click.formatting.HelpFormatter()
        param_records = [
            p.get_help_record(ctx) for p in command.get_params(ctx) if p.name != "help"
        ]
        formatter.write_dl([pr for pr in param_records if pr])
        return formatter.getvalue()


class ComponentTypeInternalMetadata(TypedDict):
    summary: Optional[str]
    description: Optional[str]
    scaffold_params_schema: Optional[Any]  # json schema
    component_params_schema: Optional[Any]  # json schema


class ComponentTypeMetadata(ComponentTypeInternalMetadata):
    name: str
    package: str


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
        component_types: dict[str, type[Component]] = {}
        for entry_point in get_entry_points_from_python_environment(COMPONENTS_ENTRY_POINT_GROUP):
            # Skip built-in entry points that are not the specified builtin component library.
            if (
                entry_point.name.startswith(BUILTIN_COMPONENTS_ENTRY_POINT_BASE)
                and not entry_point.name == builtin_component_lib
            ):
                continue

            root_module = entry_point.load()
            if not isinstance(root_module, ModuleType):
                raise DagsterError(
                    f"Invalid entry point {entry_point.name} in group {COMPONENTS_ENTRY_POINT_GROUP}. "
                    f"Value expected to be a module, got {root_module}."
                )
            for component_type in get_registered_component_types_in_module(root_module):
                key = f"{entry_point.name}.{get_component_type_name(component_type)}"
                component_types[key] = component_type

        return cls(component_types)

    def __init__(self, component_types: dict[str, type[Component]]):
        self._component_types: dict[str, type[Component]] = copy.copy(component_types)

    @staticmethod
    def empty() -> "ComponentTypeRegistry":
        return ComponentTypeRegistry({})

    def register(self, name: str, component_type: type[Component]) -> None:
        if name in self._component_types:
            raise DagsterError(f"There is an existing component registered under {name}")
        self._component_types[name] = component_type

    def has(self, name: str) -> bool:
        return name in self._component_types

    def get(self, name: str) -> type[Component]:
        return self._component_types[name]

    def keys(self) -> Iterable[str]:
        return self._component_types.keys()

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
    resources: Mapping[str, object]
    registry: ComponentTypeRegistry
    decl_node: Optional[ComponentDeclNode]
    templated_value_resolver: TemplatedValueResolver

    @staticmethod
    def for_test(
        *,
        resources: Optional[Mapping[str, object]] = None,
        registry: Optional[ComponentTypeRegistry] = None,
        decl_node: Optional[ComponentDeclNode] = None,
    ) -> "ComponentLoadContext":
        return ComponentLoadContext(
            resources=resources or {},
            registry=registry or ComponentTypeRegistry.empty(),
            decl_node=decl_node,
            templated_value_resolver=TemplatedValueResolver.default(),
        )

    @property
    def path(self) -> Path:
        from dagster_components.core.component_decl_builder import YamlComponentDecl

        if not isinstance(self.decl_node, YamlComponentDecl):
            check.failed(f"Unsupported decl_node type {type(self.decl_node)}")

        return self.decl_node.path

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "ComponentLoadContext":
        return dataclasses.replace(
            self,
            templated_value_resolver=self.templated_value_resolver.with_scope(**rendering_scope),
        )

    def for_decl_node(self, decl_node: ComponentDeclNode) -> "ComponentLoadContext":
        return dataclasses.replace(self, decl_node=decl_node)

    def _raw_params(self) -> Optional[Mapping[str, Any]]:
        from dagster_components.core.component_decl_builder import YamlComponentDecl

        if not isinstance(self.decl_node, YamlComponentDecl):
            check.failed(f"Unsupported decl_node type {type(self.decl_node)}")
        return self.decl_node.component_file_model.params

    def load_params(self, params_schema: type[T]) -> T:
        from dagster_components.core.component_decl_builder import YamlComponentDecl

        with pushd(str(self.path)):
            preprocessed_params = self.templated_value_resolver.resolve_params(
                self._raw_params(), params_schema
            )
            yaml_decl = cast(YamlComponentDecl, self.decl_node)

            if yaml_decl.source_position_tree:
                source_position_tree_of_params = yaml_decl.source_position_tree.children["params"]
                with enrich_validation_errors_with_source_position(
                    source_position_tree_of_params, ["params"]
                ):
                    return TypeAdapter(params_schema).validate_python(preprocessed_params)
            else:
                return TypeAdapter(params_schema).validate_python(preprocessed_params)


COMPONENT_REGISTRY_KEY_ATTR = "__dagster_component_registry_key"


def component_type(cls: Optional[type[Component]] = None, *, name: Optional[str] = None) -> Any:
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
