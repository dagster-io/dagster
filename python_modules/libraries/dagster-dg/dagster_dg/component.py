import copy
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

import dagster_shared.check as check
from dagster_shared.serdes import deserialize_value, serialize_value
from dagster_shared.serdes.objects import ComponentTypeSnap, LibraryObjectKey, LibraryObjectSnap

from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


class RemoteLibraryObjectRegistry:
    @staticmethod
    def from_dg_context(
        dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "RemoteLibraryObjectRegistry":
        """Fetches the set of available library objects. The default set includes everything
        discovered under the "dagster_dg.library" entry point group in the target environment. If
        `extra_modules` is provided, these will also be searched for component types.
        """
        if dg_context.use_dg_managed_environment:
            dg_context.ensure_uv_lock()

        if dg_context.config.cli.use_component_modules:
            object_data = _load_module_library_objects(
                dg_context, dg_context.config.cli.use_component_modules
            )
        else:
            object_data = _load_entry_point_components(dg_context)

        if extra_modules:
            object_data.update(_load_module_library_objects(dg_context, extra_modules))

        return RemoteLibraryObjectRegistry(object_data)

    def __init__(self, components: dict[LibraryObjectKey, LibraryObjectSnap]):
        self._objects: dict[LibraryObjectKey, LibraryObjectSnap] = copy.copy(components)

    @staticmethod
    def empty() -> "RemoteLibraryObjectRegistry":
        return RemoteLibraryObjectRegistry({})

    def get(self, key: LibraryObjectKey) -> LibraryObjectSnap:
        """Resolves a library object within the scope of a given component directory."""
        return self._objects[key]

    def get_component_type(self, key: LibraryObjectKey) -> ComponentTypeSnap:
        """Resolves a component type within the scope of a given component directory."""
        obj = self.get(key)
        if not isinstance(obj, ComponentTypeSnap):
            raise ValueError(f"Expected component type, got {obj}")
        return obj

    def has(self, key: LibraryObjectKey) -> bool:
        return key in self._objects

    def keys(self) -> Iterable[LibraryObjectKey]:
        yield from sorted(self._objects.keys(), key=lambda k: k.to_typename())

    def items(self) -> Iterable[tuple[LibraryObjectKey, LibraryObjectSnap]]:
        yield from self._objects.items()

    def __repr__(self) -> str:
        return f"<RemoteLibraryObjectRegistry {list(self._objects.keys())}>"


def all_components_schema_from_dg_context(dg_context: "DgContext") -> Mapping[str, Any]:
    """Generate a schema for all components in the current environment, or retrieve it from the cache."""
    schema_raw = None
    if dg_context.has_cache:
        cache_key = dg_context.get_cache_key("all_components_schema")
        schema_raw = dg_context.cache.get(cache_key)

    if not schema_raw:
        schema_raw = dg_context.external_components_command(["list", "all-components-schema"])
    return json.loads(schema_raw)


# ########################
# ##### HELPERS
# ########################


def _load_entry_point_components(
    dg_context: "DgContext",
) -> dict[LibraryObjectKey, LibraryObjectSnap]:
    if dg_context.has_cache:
        cache_key = dg_context.get_cache_key("component_registry_data")
        raw_registry_data = dg_context.cache.get(cache_key)
    else:
        cache_key = None
        raw_registry_data = None

    if not raw_registry_data:
        raw_registry_data = dg_context.external_components_command(["list", "library"])
        if dg_context.has_cache and cache_key and is_valid_json(raw_registry_data):
            dg_context.cache.set(cache_key, raw_registry_data)

    return _parse_raw_registry_data(raw_registry_data)


def _load_module_library_objects(
    dg_context: "DgContext", modules: Sequence[str]
) -> dict[LibraryObjectKey, LibraryObjectSnap]:
    modules_to_fetch = set(modules)
    data: dict[LibraryObjectKey, LibraryObjectSnap] = {}
    if dg_context.has_cache:
        for module in modules:
            cache_key = dg_context.get_cache_key_for_module(module)
            raw_data = dg_context.cache.get(cache_key)
            if raw_data:
                data.update(_parse_raw_registry_data(raw_data))
                modules_to_fetch.remove(module)

    if modules_to_fetch:
        raw_local_object_data = dg_context.external_components_command(
            [
                "list",
                "library",
                "--no-entry-points",
                *modules_to_fetch,
            ]
        )
        all_fetched_objects = _parse_raw_registry_data(raw_local_object_data)
        for module in modules_to_fetch:
            objects = {k: v for k, v in all_fetched_objects.items() if k.namespace == module}
            data.update(objects)

            if dg_context.has_cache:
                cache_key = dg_context.get_cache_key_for_module(module)
                dg_context.cache.set(cache_key, _dump_raw_registry_data(objects))

    return data


def _parse_raw_registry_data(
    raw_registry_data: str,
) -> dict[LibraryObjectKey, LibraryObjectSnap]:
    deserialized = check.is_list(deserialize_value(raw_registry_data), of_type=LibraryObjectSnap)
    return {obj.key: obj for obj in deserialized}


def _dump_raw_registry_data(
    registry_data: Mapping[LibraryObjectKey, LibraryObjectSnap],
) -> str:
    return serialize_value(list(registry_data.values()))
