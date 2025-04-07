import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence, Set
from typing import TYPE_CHECKING, Any, Optional, Union

import dagster_shared.check as check
from dagster_shared.serdes import deserialize_value, serialize_value
from dagster_shared.serdes.objects import PackageObjectKey, PackageObjectSnap
from dagster_shared.serdes.objects.package_entry import PackageObjectFeature

from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


class RemotePackageRegistry:
    @staticmethod
    def from_dg_context(
        dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "RemotePackageRegistry":
        """Fetches the set of available package entries. The default set includes everything
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

        return RemotePackageRegistry(object_data)

    def __init__(self, components: dict[PackageObjectKey, PackageObjectSnap]):
        self._objects: dict[PackageObjectKey, PackageObjectSnap] = copy.copy(components)

    @staticmethod
    def empty() -> "RemotePackageRegistry":
        return RemotePackageRegistry({})

    @property
    def packages(self) -> Set[str]:
        return {key.package for key in self._objects.keys()}

    def package_entries(self, package: str) -> Set[PackageObjectKey]:
        return {key for key in self._objects.keys() if key.package == package}

    def get_objects(
        self, package: Optional[str] = None, feature: Optional[PackageObjectFeature] = None
    ) -> Sequence[PackageObjectSnap]:
        return [
            entry
            for entry in self._objects.values()
            if (package is None or package == entry.key.package)
            and (feature is None or feature in entry.features)
        ]

    def get(self, key: PackageObjectKey) -> PackageObjectSnap:
        """Resolves a library object within the scope of a given component directory."""
        return self._objects[key]

    def has(self, key: PackageObjectKey) -> bool:
        return key in self._objects

    def keys(self) -> Iterable[PackageObjectKey]:
        yield from sorted(self._objects.keys(), key=lambda k: k.to_typename())

    def items(self) -> Iterable[tuple[PackageObjectKey, PackageObjectSnap]]:
        yield from self._objects.items()

    def __repr__(self) -> str:
        return f"<RemotePackageRegistry {list(self._objects.keys())}>"


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
) -> dict[PackageObjectKey, PackageObjectSnap]:
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
) -> dict[PackageObjectKey, PackageObjectSnap]:
    modules_to_fetch = set(modules)
    data: dict[PackageObjectKey, PackageObjectSnap] = {}
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
) -> dict[PackageObjectKey, PackageObjectSnap]:
    deserialized = check.is_list(deserialize_value(raw_registry_data), of_type=PackageObjectSnap)
    return {obj.key: obj for obj in deserialized}


def _dump_raw_registry_data(
    registry_data: Mapping[PackageObjectKey, PackageObjectSnap],
) -> str:
    return serialize_value(list(registry_data.values()))


def get_specified_env_var_deps(component_data: Mapping[str, Any]) -> set[str]:
    if not component_data.get("requirements") or "env" not in component_data["requirements"]:
        return set()
    return set(component_data["requirements"]["env"])


env_var_regex = re.compile(r"\{\{\s*env\(\s*['\"]([^'\"]+)['\"]\)\s*\}\}")


def get_used_env_vars(data_structure: Union[Mapping[str, Any], Sequence[Any], Any]) -> set[str]:
    if isinstance(data_structure, Mapping):
        return set.union(set(), *(get_used_env_vars(value) for value in data_structure.values()))
    elif isinstance(data_structure, str):
        return set(env_var_regex.findall(data_structure))
    elif isinstance(data_structure, Sequence):
        return set.union(set(), *(get_used_env_vars(item) for item in data_structure))
    else:
        return set()
