import contextlib
import contextvars
import dataclasses
import importlib
import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple, Optional, Union

from dagster_shared.serdes.serdes import whitelist_for_serdes
from dagster_shared.yaml_utils.source_position import SourcePositionTree
from typing_extensions import TypeAlias

from dagster._annotations import PublicAttr, preview, public
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import DagsterError
from dagster._utils import pushd
from dagster._utils.cached_method import cached_method
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils import get_path_from_module


class ComponentsJobHandle(NamedTuple):
    name: str


# Represents a sort of definition we may request in a run.
ComponentsDefinitionHandle: TypeAlias = Union[AssetKey, AssetCheckKey, ComponentsJobHandle]


@whitelist_for_serdes
@dataclass
class ComponentsLoadData:
    """Data associated with a component load.

    defs_by_component stores the set of definitions that are provided by each component.
    data_by_component stores arbitrary data associated with a component, that subset
    loads may need to access. For now, just caches asset selections.
    """

    defs_by_component: dict[str, list[ComponentsDefinitionHandle]]
    data_by_component: dict[str, Any]


class ComponentsLoadType(str, Enum):
    """Type of load that is being performed."""

    INITIAL_LOAD = "initial_load"
    SUBSET_LOAD = "subset_load"


@public
@preview(emit_runtime_warning=False)
@dataclass
class ComponentLoadContext:
    """Context for loading a single component."""

    defs_to_load: Optional[Sequence[ComponentsDefinitionHandle]]
    path: PublicAttr[Path]
    project_root: PublicAttr[Path]
    defs_module_path: PublicAttr[Path]
    defs_module_name: PublicAttr[str]
    resolution_context: PublicAttr[ResolutionContext]
    load_data: ComponentsLoadData
    load_type: PublicAttr[ComponentsLoadType]

    @staticmethod
    def current() -> "ComponentLoadContext":
        context = active_component_load_context.get()
        if context is None:
            raise DagsterError(
                "No active component load context, `ComponentLoadContext.current()` must be called inside of a component's `build_defs` method"
            )
        return context

    @staticmethod
    def for_module(
        defs_module: ModuleType, project_root: Path, load_data: Optional[ComponentsLoadData]
    ) -> "ComponentLoadContext":
        path = get_path_from_module(defs_module)
        ctx = ComponentLoadContext(
            path=path,
            project_root=project_root,
            defs_module_path=path,
            defs_module_name=defs_module.__name__,
            resolution_context=ResolutionContext.default(),
            # Hardcoded right now. We would need to pipe in the list of defs from the run request.
            defs_to_load=[AssetKey("asset_three")],
            load_data=load_data
            or ComponentsLoadData(
                defs_by_component={},
                data_by_component={},
            ),
            load_type=ComponentsLoadType.INITIAL_LOAD
            if not load_data
            else ComponentsLoadType.SUBSET_LOAD,
        )
        if load_data:
            print("LOADING SUBSET OF COMPONENTS")
            keys = ctx.get_component_cache_keys_to_load()
            print("- " + "\n- ".join(keys))
        return ctx

    @staticmethod
    def for_test() -> "ComponentLoadContext":
        return ComponentLoadContext(
            path=Path.cwd(),
            project_root=Path.cwd(),
            defs_module_path=Path.cwd(),
            defs_module_name="test",
            resolution_context=ResolutionContext.default(),
            defs_to_load=None,
            load_data=ComponentsLoadData(
                defs_by_component={},
                data_by_component={},
            ),
            load_type=ComponentsLoadType.INITIAL_LOAD,
        )

    def _with_resolution_context(
        self, resolution_context: ResolutionContext
    ) -> "ComponentLoadContext":
        return dataclasses.replace(self, resolution_context=resolution_context)

    def with_rendering_scope(self, rendering_scope: Mapping[str, Any]) -> "ComponentLoadContext":
        return self._with_resolution_context(
            self.resolution_context.with_scope(
                **rendering_scope,
                **{
                    "project_root": str(self.project_root.resolve()),
                },
            )
        )

    def with_source_position_tree(
        self, source_position_tree: SourcePositionTree
    ) -> "ComponentLoadContext":
        return self._with_resolution_context(
            self.resolution_context.with_source_position_tree(source_position_tree)
        )

    def for_path(self, path: Path) -> "ComponentLoadContext":
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

    def load_defs(self, module: ModuleType) -> Definitions:
        """Builds the set of Dagster definitions for a component module.

        This is useful for resolving dependencies on other components.
        """
        # FIXME: This should go through the component loader system
        # to allow for this value to be cached and more selectively
        # loaded. This is just a temporary hack to keep tests passing.
        from dagster.components.core.load_defs import load_defs

        return load_defs(module, self.project_root)

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

    ############################################################
    # MANIPULATE OR RETRIEVE COMPONENT-SPECIFIC CACHED DATA
    ############################################################

    def get_partial_data_for_current_component(self) -> Any:
        if self.load_type == ComponentsLoadType.SUBSET_LOAD:
            raise Exception("Cannot get partial data for current component on subset load")
        key = self.get_component_cache_key()
        return self.load_data.data_by_component.get(key, None)

    def get_data_for_current_component(self) -> Any:
        if self.load_type == ComponentsLoadType.INITIAL_LOAD:
            raise Exception("Cannot get data for current component on initial load")
        key = self.get_component_cache_key()
        return self.load_data.data_by_component[key]

    def record_component_data(self, data: Any) -> None:
        if self.load_type == ComponentsLoadType.SUBSET_LOAD:
            raise Exception("Cannot record data for current component on subset load")
        key = self.get_component_cache_key()
        self.load_data.data_by_component[key] = data

    ############################################################
    # MANIPULATE OR RETRIEVE DEFS PROVIDED BY COMPONENTS
    ############################################################

    def record_component_defs(self, defs: Definitions) -> None:
        if self.load_type == ComponentsLoadType.SUBSET_LOAD:
            raise Exception("Cannot record component defs on subset load")
        all_asset_keys = set(
            itertools.chain.from_iterable(
                ([asset.key] if isinstance(asset, AssetSpec) else asset.keys)
                for asset in (defs.assets or [])
                if isinstance(asset, (AssetSpec, AssetsDefinition))
            )
        )
        all_asset_checks = set(
            itertools.chain.from_iterable([check.check_keys for check in (defs.asset_checks or [])])
        )
        all_job_names = set(ComponentsJobHandle(name=job.name) for job in (defs.jobs or []))
        key = self.get_component_cache_key()
        self.load_data.defs_by_component[key] = list(
            all_asset_keys | all_asset_checks | all_job_names
        )

    @cached_method
    def get_component_paths_by_key(self) -> dict[ComponentsDefinitionHandle, set[Path]]:
        if self.load_type == ComponentsLoadType.INITIAL_LOAD:
            raise Exception("Cannot get component paths by key on initial load")
        output = {}
        for key, defs in self.load_data.defs_by_component.items():
            for def_handle in defs:
                output.setdefault(def_handle, set()).add(key)
        return output

    @cached_method
    def get_component_cache_keys_to_load(self) -> set[str]:
        if self.load_type == ComponentsLoadType.INITIAL_LOAD or not self.defs_to_load:
            raise Exception("Cannot get component paths by key on initial load")
        keys_to_load = set()
        for def_handle in self.defs_to_load:
            for key in self.get_component_paths_by_key()[def_handle]:
                keys_to_load.add(key)
        return keys_to_load

    def should_load_component_path(self, path: Path) -> bool:
        """Whether we ought to load the component defined at the given path.
        True unless we are in a subset load, in which case we only load the components
        that are necessary to load the needed definitions.
        """
        if self.load_type == ComponentsLoadType.INITIAL_LOAD:
            return True
        return (
            "/".join(tuple(path.relative_to(self.project_root).parts))
            in self.get_component_cache_keys_to_load()
        )

    @cached_method
    def get_component_cache_key(self) -> str:
        return "/".join(tuple(self.path.relative_to(self.project_root).parts))


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
