import importlib.util
import itertools
import os
import sys
from abc import ABC, abstractmethod
<<<<<<< HEAD
from dataclasses import dataclass, replace
=======
from dataclasses import dataclass, field, replace
from functools import cache, cached_property
>>>>>>> 5ce02703d8 (cp)
from pathlib import Path
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Final,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

from dagster_tests.cli_tests.workspace_tests.definitions_test_cases import defs_file
from pydantic import BaseModel
from typing_extensions import Self

from dagster._core.errors import DagsterError
from dagster._record import record
from dagster._utils import snakecase
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


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
    def from_component_params(
        cls, init_context: "ComponentLoadContext", component_params: object
    ) -> Self: ...


def is_inside_deployment_project(path: Path) -> bool:
    try:
        _resolve_deployment_root_path(path)
        return True
    except DagsterError:
        return False


def _resolve_deployment_root_path(path: Path) -> str:
    current_path = os.path.abspath(path)
    while not _is_deployment_root(current_path):
        current_path = os.path.dirname(current_path)
        if current_path == "/":
            raise DagsterError("Cannot find deployment root")
    return current_path


def is_inside_code_location_project(path: Path) -> bool:
    try:
        _resolve_code_location_root_path(path)
        return True
    except DagsterError:
        return False


def _resolve_code_location_root_path(path: Path) -> str:
    current_path = os.path.abspath(path)
    while not _is_code_location_root(current_path):
        current_path = os.path.dirname(current_path)
        if current_path == "/":
            raise DagsterError("Cannot find code location root")
    return current_path


def _is_deployment_root(path: str) -> bool:
    return os.path.exists(os.path.join(path, "code_locations"))


def _is_code_location_root(path: str) -> bool:
    return os.path.basename(os.path.dirname(path)) == "code_locations"


# Deployment
_DEPLOYMENT_CODE_LOCATIONS_DIR: Final = "code_locations"

# Code location
_CODE_LOCATION_CUSTOM_COMPONENTS_DIR: Final = "lib"
_CODE_LOCATION_COMPONENT_INSTANCES_DIR: Final = "components"


class DeploymentProjectContext:
    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls(root_path=_resolve_deployment_root_path(path))

    def __init__(self, root_path: str):
        self._root_path = root_path

    @property
    def deployment_root(self) -> str:
        return self._root_path

    @property
    def code_location_root_path(self) -> str:
        return os.path.join(self._root_path, _DEPLOYMENT_CODE_LOCATIONS_DIR)

    def has_code_location(self, name: str) -> bool:
        return os.path.exists(os.path.join(self._root_path, "code_locations", name))


class CodeLocationProjectContext:
    @classmethod
    def from_path(cls, path: Path, component_registry: "ComponentRegistry") -> Self:
        root_path = _resolve_code_location_root_path(path)
        name = os.path.basename(root_path)

        # TODO: Rm when a more robust solution is implemented
        # Make sure we can import from the cwd
        if sys.path[0] != "":
            sys.path.insert(0, "")

        components_lib_module = f"{name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"
        module = importlib.import_module(components_lib_module)
        register_components_in_module(component_registry, module)

        return cls(
            deployment_context=DeploymentProjectContext.from_path(path),
            root_path=root_path,
            name=os.path.basename(root_path),
            component_registry=component_registry,
        )

    def __init__(
        self,
        deployment_context: DeploymentProjectContext,
        root_path: str,
        name: str,
        component_registry: "ComponentRegistry",
    ):
        self._deployment_context = deployment_context
        self._root_path = root_path
        self._name = name
        self._component_registry = component_registry

    @property
    def deployment_context(self) -> DeploymentProjectContext:
        return self._deployment_context

    @property
    def component_types_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_CUSTOM_COMPONENTS_DIR)

    @property
    def component_types_root_module(self) -> str:
        return f"{self._name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"

    @property
    def component_registry(self) -> "ComponentRegistry":
        return self._component_registry

    def has_component_type(self, name: str) -> bool:
        return self._component_registry.has(name)

    def get_component_type(self, name: str) -> Type[Component]:
        if not self.has_component_type(name):
            raise DagsterError(f"No component type named {name}")
        return self._component_registry.get(name)

    def get_component_instance_path(self, name: str) -> str:
        if name not in self.component_instances:
            raise DagsterError(f"No component instance named {name}")
        return os.path.join(self.component_instances_root_path, name)

    @property
    def component_instances_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR)

    @property
    def component_instances(self) -> Iterable[str]:
        return os.listdir(
            os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR)
        )

    def has_component_instance(self, name: str) -> bool:
        return os.path.exists(
            os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR, name)
        )


class ComponentRegistry:
    def __init__(self, components: Dict[str, Type[Component]]):
        self._components: Dict[str, Type[Component]] = components

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


class DefsFileModel(BaseModel):
    component_type: str
    component_params: Optional[Mapping[str, Any]] = None


from dagster import _check as check


@dataclass
class ComponentInitContext:
    # def __init__(self, *, path: Path, registry: Optional[ComponentRegistry] = None):
    #     self.path = path
    #     self.registry = registry or ComponentRegistry()

    path: Path
    registry: ComponentRegistry

    def for_path(self, path: Path) -> "ComponentInitContext":
        return replace(self, path=path)

    @property
    def defs_path(self) -> Path:
        return self.path / "defs.yml"

    @cached_property
    def has_defs_yamls(self) -> bool:
        return self.defs_path.exists()

    def get_parsed_defs(self) -> DefsFileModel:
        check.invariant(self.has_defs_yamls, "No defs.yml found")
        return parse_yaml_file_to_pydantic(
            DefsFileModel, self.defs_path.read_text(), str(self.path)
        )

    # def load(self) -> Sequence[Component]:
    #     if self.has_defs_yamls:
    #         parsed_defs = self.get_parsed_defs()
    #         component_type = self.registry.get(parsed_defs.component_type)
    #         return [component_type.from_component_params(self, parsed_defs.component_params)]
    #     else:
    #         return list(
    #             itertools.chain(*(self.for_path(subpath).load() for subpath in self.path.iterdir()))
    #         )


class ComponentDecl: ...


@record
class YamlComponentInstance(ComponentDecl):
    path: Path
    defs_file_model: DefsFileModel


@record
class ComponentFolder(ComponentDecl):
    path: Path
    sub_components: Sequence[Union[YamlComponentInstance, "ComponentFolder"]]


def find_component_decl(context: ComponentInitContext) -> Optional[ComponentDecl]:
    # right now, we only support two types of components, both of which are folders
    # if the folder contains a defs.yml file, it's a component instance
    # otherwise, it's a folder containing sub-components

    if not context.path.is_dir():
        return None

    defs_path = context.path / "defs.yml"

    if defs_path.exists():
        defs_file_model = parse_yaml_file_to_pydantic(
            DefsFileModel, defs_path.read_text(), str(context.path)
        )
        return YamlComponentInstance(path=context.path, defs_file_model=defs_file_model)

    subs = []
    for subpath in context.path.iterdir():
        component = find_component_decl(context.for_path(subpath))
        if component:
            subs.append(component)

    return ComponentFolder(path=context.path, sub_components=subs) if subs else None


def build_component_hierarchy(
    context: ComponentLoadContext, component_folder: ComponentFolder
) -> Sequence[Component]:
    for component in component_folder.sub_components:
        if isinstance(component, YamlComponentInstance):
            parsed_defs = component.defs_file_model
            component_type = context.registry.get(parsed_defs.component_type)
            return [component_type.from_component_params(self, parsed_defs.component_params)]
        elif isinstance(component, ComponentFolder):
            ...
        else:
            raise NotImplementedError(f"Unknown component type {component}")

    return [
        component
        for sub_component in component_folder.sub_components
        for component in build_component_hierarchy(context, sub_component)
    ]


def build_defs_from_component_folder(
    path: Path,
    registry: ComponentRegistry,
    resources: Mapping[str, object],
) -> "Definitions":
    """Build a definitions object from a folder within the components hierarchy."""
    from dagster._core.definitions.definitions_class import Definitions

    init_context = ComponentInitContext(path=path, registry=registry)
    component_folder = find_component_decl(init_context)
    assert isinstance(component_folder, ComponentFolder)

    return Definitions.merge_internal(
        *[c.build_defs(ComponentLoadContext(resources)) for c in component_folder.sub_components]
    )


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


# Public method so optional Nones are fine
def build_defs_from_toplevel_components_folder(
    path: Path,
    resources: Optional[Mapping[str, object]] = None,
    registry: Optional["ComponentRegistry"] = None,
) -> "Definitions":
    """Build a Definitions object from an entire component hierarchy."""
    from dagster._core.definitions.definitions_class import Definitions

    context = CodeLocationProjectContext.from_path(path, registry or ComponentRegistry.empty())

    all_defs: List[Definitions] = []
    for component in context.component_instances:
        component_path = Path(context.get_component_instance_path(component))
        defs = build_defs_from_component_folder(
            path=component_path,
            registry=context.component_registry,
            resources=resources or {},
        )
        all_defs.append(defs)
    return Definitions.merge_internal(*all_defs)
