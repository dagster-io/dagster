import copy
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


@dataclass
class RemoteComponentType:
    name: str
    package: str
    summary: Optional[str]
    description: Optional[str]
    scaffold_params_schema: Optional[Mapping[str, Any]]  # json schema
    component_params_schema: Optional[Mapping[str, Any]]  # json schema

    @property
    def key(self) -> str:
        return self.name


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
) -> Mapping[str, Mapping[str, Mapping[str, Any]]]:
    paths_to_fetch = set(paths)
    data_for_path: dict[str, dict[str, Mapping[str, Any]]] = {}
    if dg_context.has_cache:
        for path in paths:
            cache_key = dg_context.get_cache_key_for_local_components(path)
            raw_data = dg_context.cache.get(cache_key)
            if raw_data:
                data_for_path[str(path)] = json.loads(raw_data)
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
            data_for_path[str(path)] = local_component_data.get(str(path), {})

        if dg_context.has_cache:
            for path in paths_to_fetch:
                cache_key = dg_context.get_cache_key_for_local_components(path)
                data_for_path_json = json.dumps(local_component_data.get(str(path), {}))
                if cache_key and is_valid_json(data_for_path_json):
                    dg_context.cache.set(cache_key, data_for_path_json)

    return data_for_path


class RemoteComponentRegistry:
    @classmethod
    def from_dg_context(
        cls, dg_context: "DgContext", local_component_type_dirs: Optional[Sequence[Path]] = None
    ) -> "RemoteComponentRegistry":
        """Fetches the set of available component types, including local component types for the
        specified directories. Caches the result if possible.
        """
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

        registry_data = json.loads(raw_registry_data)

        local_component_data: Mapping[str, Mapping[str, Mapping[str, Any]]] = {}
        if local_component_type_dirs:
            local_component_data = _retrieve_local_component_types(
                dg_context, local_component_type_dirs
            )
        return cls.from_dict(
            global_component_types=registry_data, local_component_types=local_component_data
        )

    @classmethod
    def from_dict(
        cls,
        global_component_types: Mapping[str, Mapping[str, Any]],
        local_component_types: Mapping[str, Mapping[str, Mapping[str, Any]]],
    ) -> "RemoteComponentRegistry":
        components_by_path = defaultdict(dict)
        for directory in local_component_types:
            for key, metadata in local_component_types[directory].items():
                components_by_path[directory][key] = RemoteComponentType(**metadata)

        return RemoteComponentRegistry(
            {key: RemoteComponentType(**value) for key, value in global_component_types.items()},
            local_components=components_by_path,
        )

    def __init__(
        self,
        components: dict[str, RemoteComponentType],
        local_components: dict[str, dict[str, RemoteComponentType]],
    ):
        self._components: dict[str, RemoteComponentType] = copy.copy(components)
        self._local_components: dict[str, dict[str, RemoteComponentType]] = copy.copy(
            local_components
        )

    @staticmethod
    def empty() -> "RemoteComponentRegistry":
        return RemoteComponentRegistry({}, {})

    def has_global(self, name: str) -> bool:
        return name in self._components

    def get(self, path: Path, key: str) -> RemoteComponentType:
        """Resolves a component type within the scope of a given component directory."""
        if key in self._components:
            return self._components[key]

        return self._local_components[str(path)][key]

    def get_global(self, name: str) -> RemoteComponentType:
        return self._components[name]

    def global_keys(self) -> Iterable[str]:
        return self._components.keys()

    def global_items(self) -> Iterable[tuple[str, RemoteComponentType]]:
        for key in sorted(self.global_keys()):
            yield key, self.get_global(key)

    def __repr__(self) -> str:
        return f"<RemoteComponentRegistry {list(self._components.keys())}>"
