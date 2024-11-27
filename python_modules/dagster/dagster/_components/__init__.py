import importlib.util
import itertools
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Final,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Type,
    cast,
)

from pydantic import BaseModel
from typing_extensions import Self

from dagster._core.errors import DagsterError
from dagster._utils import snakecase
from dagster._utils.pydantic_yaml import parse_yaml_file_to_pydantic

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


class Component(ABC):
    name: ClassVar[Optional[str]] = None

    @classmethod
    def registered_name(cls):
        return cls.name or snakecase(cls.__name__)

    @classmethod
    def generate_files(cls) -> None:
        raise NotImplementedError()

    @abstractmethod
    def build_defs(self, context: "ComponentLoadContext") -> "Definitions": ...

    @classmethod
    @abstractmethod
    def from_component_params(
        cls, init_context: "ComponentInitContext", component_params: object
    ) -> Self: ...

    @classmethod
    def loadable_paths(cls, path: Path) -> Sequence[Path]:
        return [path]


class FileCollectionComponent(Component):
    """Convenience class for defining components which operate independently on files within
    a subdirectory.
    """

    @abstractmethod
    def loadable_paths(self) -> Sequence[Path]:
        """Returns the paths within the subdirectory that should be loaded by this component."""
        ...

    @abstractmethod
    def build_defs_for_path(
        self, path: Path, load_context: "ComponentLoadContext"
    ) -> "Definitions": ...

    def build_defs(self, load_context: "ComponentLoadContext") -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        return Definitions.merge(
            *(self.build_defs_for_path(path, load_context) for path in self.loadable_paths())
        )


def is_inside_deployment_project(path: str = ".") -> bool:
    try:
        _resolve_deployment_root_path(path)
        return True
    except DagsterError:
        return False


def _resolve_deployment_root_path(path: str) -> str:
    current_path = os.path.abspath(path)
    while not _is_deployment_root(current_path):
        current_path = os.path.dirname(current_path)
        if current_path == "/":
            raise DagsterError("Cannot find deployment root")
    return current_path


def is_inside_code_location_project(path: str = ".") -> bool:
    try:
        _resolve_code_location_root_path(path)
        return True
    except DagsterError:
        return False


def _resolve_code_location_root_path(path: str) -> str:
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
    def from_path(cls, path: str) -> Self:
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
    def from_path(cls, path: str) -> Self:
        root_path = _resolve_code_location_root_path(path)
        name = os.path.basename(root_path)
        component_registry = ComponentRegistry()

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

    def has_component_type(self, name: str) -> bool:
        return self._component_registry.has(name)

    def get_component_type(self, name: str) -> Type[Component]:
        if not self.has_component_type(name):
            raise DagsterError(f"No component type named {name}")
        return self._component_registry.get(name)

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
    def __init__(self):
        self._components: Dict[str, Type[Component]] = {}

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

    def __repr__(self):
        return f"<ComponentRegistry {list(self._components.keys())}>"


class ComponentLoadContext:
    def __init__(self, resources: Mapping[str, object] = {}):
        self.resources = resources


class DefsFileModel(BaseModel):
    component_type: str
    component_params: Optional[Mapping[str, Any]] = None


@dataclass
class ComponentInitContext:
    path: Path
    registry: ComponentRegistry = field(default_factory=lambda: ComponentRegistry())

    def for_path(self, path: Path) -> "ComponentInitContext":
        return replace(self, path=path)

    def get_parsed_defs(self) -> Optional[DefsFileModel]:
        defs_path = self.path / "defs.yml"
        if defs_path.exists():
            return parse_yaml_file_to_pydantic(DefsFileModel, defs_path.read_text(), str(self.path))
        else:
            return None

    def load(self) -> Sequence[Component]:
        if not self.path.is_dir():
            return []

        parsed_defs = self.get_parsed_defs()
        if parsed_defs:
            component_type = cast(Type[Component], self.registry.get(parsed_defs.component_type))
            return [component_type.from_component_params(self, parsed_defs.component_params)]
        else:
            return list(
                itertools.chain(*(self.for_path(subpath).load() for subpath in self.path.iterdir()))
            )


def build_defs_from_path(
    path: Path,
    registry: ComponentRegistry,
    resources: Mapping[str, object],
) -> "Definitions":
    from dagster._core.definitions.definitions_class import Definitions

    init_context = ComponentInitContext(path=path, registry=registry)
    components = init_context.load()
    return Definitions.merge(*[c.build_defs(ComponentLoadContext(resources)) for c in components])


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
