import copy
import json
from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


@dataclass(frozen=True)
class RemoteComponentKey:
    name: str
    package: str

    @abstractmethod
    def to_string(self) -> str: ...

    @staticmethod
    def from_identifier(identifier: str, dirpath: Path) -> "RemoteComponentKey":
        if identifier.endswith(".py"):
            name, package = identifier.split("@")
            return LocalRemoteComponentKey(name=name, package=package, path=str(dirpath / package))
        else:
            return GlobalRemoteComponentKey.from_identifier(identifier)


@dataclass(frozen=True)
class GlobalRemoteComponentKey(RemoteComponentKey):
    def to_string(self) -> str:
        return f"{self.name}@{self.package}"

    @staticmethod
    def from_identifier(identifier: str) -> "GlobalRemoteComponentKey":
        name, package = identifier.split("@")
        return GlobalRemoteComponentKey(name=name, package=package)


@dataclass(frozen=True)
class LocalRemoteComponentKey(RemoteComponentKey):
    path: str

    def to_string(self) -> str:
        return f"{self.name}@{self.package} ({self.path})"


@dataclass
class RemoteComponentType:
    name: str
    package: str
    summary: Optional[str]
    description: Optional[str]
    scaffold_params_schema: Optional[Mapping[str, Any]]  # json schema
    component_params_schema: Optional[Mapping[str, Any]]  # json schema


def _get_remote_type_mapping_from_raw_data(
    raw_data: Mapping[str, Any],
) -> Mapping[GlobalRemoteComponentKey, RemoteComponentType]:
    data = {}
    for identifier, metadata in raw_data.items():
        data[GlobalRemoteComponentKey.from_identifier(identifier)] = RemoteComponentType(**metadata)
    return data


def _get_local_type_mapping_from_raw_data(
    raw_data: Mapping[str, Any], path: Path
) -> Mapping[LocalRemoteComponentKey, RemoteComponentType]:
    data = {}
    for identifier, metadata in raw_data.items():
        name, package = identifier.split("@")
        data[LocalRemoteComponentKey(name=name, package=package, path=str(path))] = (
            RemoteComponentType(**metadata)
        )
    return data


def all_components_schema_from_dg_context(dg_context: "DgContext") -> Mapping[str, Any]:
    """Generate a schema for all components in the current environment, or retrieve it from the cache."""
    schema_raw = None
    if dg_context.has_cache:
        cache_key = dg_context.get_cache_key("all_components_schema")
        schema_raw = dg_context.cache.get(cache_key)

    if not schema_raw:
        schema_raw = dg_context.external_components_command(["list", "all-components-schema"])
    return json.loads(schema_raw)


def _retrieve_local_component_types(
    dg_context: "DgContext", paths: Sequence[Path]
) -> Mapping[LocalRemoteComponentKey, RemoteComponentType]:
    paths_to_fetch = set(paths)
    data: dict[LocalRemoteComponentKey, RemoteComponentType] = {}
    if dg_context.has_cache:
        for path in paths:
            cache_key = dg_context.get_cache_key_for_local_components(path)
            raw_data = dg_context.cache.get(cache_key)
            if raw_data:
                data.update(_get_local_type_mapping_from_raw_data(json.loads(raw_data), path))
                paths_to_fetch.remove(path)

    if paths_to_fetch:
        raw_local_component_data = dg_context.external_components_command(
            [
                "list",
                "local-component-types",
                *[str(path) for path in paths_to_fetch],
            ]
        )
        local_component_data = json.loads(raw_local_component_data)
        for path in paths_to_fetch:
            data.update(_get_local_type_mapping_from_raw_data(local_component_data, path))

        if dg_context.has_cache:
            for path in paths_to_fetch:
                cache_key = dg_context.get_cache_key_for_local_components(path)
                data_for_path_json = json.dumps(local_component_data.get(str(path), {}))
                if cache_key and is_valid_json(data_for_path_json):
                    dg_context.cache.set(cache_key, data_for_path_json)

    return data


class RemoteComponentRegistry:
    @staticmethod
    def from_dg_context(
        dg_context: "DgContext", local_component_type_dirs: Optional[Sequence[Path]] = None
    ) -> "RemoteComponentRegistry":
        """Fetches the set of available component types, including local component types for the
        specified directories. Caches the result if possible.
        """
        component_data = {}
        if dg_context.use_dg_managed_environment:
            dg_context.ensure_uv_lock()

        if dg_context.has_cache:
            cache_key = dg_context.get_cache_key("component_registry_data")
            raw_registry_data = dg_context.cache.get(cache_key)
        else:
            cache_key = None
            raw_registry_data = None

        if not raw_registry_data:
            raw_registry_data = dg_context.external_components_command(["list", "component-types"])
            if dg_context.has_cache and cache_key and is_valid_json(raw_registry_data):
                dg_context.cache.set(cache_key, raw_registry_data)

        component_data.update(_get_remote_type_mapping_from_raw_data(json.loads(raw_registry_data)))

        if local_component_type_dirs:
            component_data.update(
                _retrieve_local_component_types(dg_context, local_component_type_dirs)
            )

        return RemoteComponentRegistry(component_data)

    def __init__(self, components: dict[RemoteComponentKey, RemoteComponentType]):
        self._components: dict[RemoteComponentKey, RemoteComponentType] = copy.copy(components)

    @staticmethod
    def empty() -> "RemoteComponentRegistry":
        return RemoteComponentRegistry({})

    def has_global(self, key: RemoteComponentKey) -> bool:
        return key in self._components

    def get(self, key: RemoteComponentKey) -> RemoteComponentType:
        """Resolves a component type within the scope of a given component directory."""
        return self._components[key]

    def get_global(self, key: GlobalRemoteComponentKey) -> RemoteComponentType:
        if not isinstance(key, GlobalRemoteComponentKey):
            raise ValueError(f"Expected GlobalRemoteComponentKey, got {key}")
        return self._components[key]

    def global_keys(self) -> Iterable[GlobalRemoteComponentKey]:
        for key in sorted(self._components.keys(), key=lambda k: k.to_string()):
            if isinstance(key, GlobalRemoteComponentKey):
                yield key

    def global_items(self) -> Iterable[tuple[GlobalRemoteComponentKey, RemoteComponentType]]:
        for key in self.global_keys():
            yield key, self.get_global(key)

    def __repr__(self) -> str:
        return f"<RemoteComponentRegistry {list(self._components.keys())}>"
