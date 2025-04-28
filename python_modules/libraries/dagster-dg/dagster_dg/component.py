import copy
import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence, Set
from typing import TYPE_CHECKING, Any, Optional, Union

import dagster_shared.check as check
from dagster_shared.error import (
    SerializableErrorInfo,
    make_simple_frames_removed_hint,
    remove_system_frames_from_error,
)
from dagster_shared.serdes import deserialize_value, serialize_value
from dagster_shared.serdes.objects import PluginObjectKey, PluginObjectSnap
from dagster_shared.serdes.objects.package_entry import PluginManifest, PluginObjectFeature
from packaging.version import Version
from rich.console import Console
from rich.panel import Panel

from dagster_dg.utils.warnings import emit_warning

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


class RemotePluginRegistry:
    @staticmethod
    def from_dg_context(
        dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "RemotePluginRegistry":
        """Fetches the set of available plugin objects. The default set includes everything
        discovered under the "dagster_dg.plugin" entry point group in the target environment. If
        `extra_modules` is provided, these will also be searched for component types.
        """
        if dg_context.use_dg_managed_environment:
            dg_context.ensure_uv_lock()

        if dg_context.config.cli.use_component_modules:
            plugin_manifest = _load_module_library_objects(
                dg_context, dg_context.config.cli.use_component_modules
            )
        else:
            plugin_manifest = _load_entry_point_components(dg_context)

        if extra_modules:
            plugin_manifest = plugin_manifest.merge(
                _load_module_library_objects(dg_context, extra_modules)
            )

        if (
            dg_context.is_plugin
            and not dg_context.config.cli.use_component_modules
            and dg_context.default_plugin_module_name not in plugin_manifest.modules
        ):
            emit_warning(
                "missing_dg_plugin_module_in_manifest",
                f"""
                Your package defines a `dagster_dg.plugin` entry point, but this module was not
                found in the plugin manifest for the current environment. This means either that
                your project is not installed in the current environment, or that the entry point
                metadata was added after your module was installed. Python entry points are
                registered at package install time. Please reinstall your package into the current
                environment to ensure the entry point is registered.

                Entry point module: `{dg_context.default_plugin_module_name}`
                """,
                suppress_warnings=dg_context.config.cli.suppress_warnings,
            )

        return RemotePluginRegistry(plugin_manifest)

    def __init__(self, plugin_manifest: PluginManifest):
        self._modules = copy.copy(plugin_manifest.modules)
        self._objects = {obj.key: obj for obj in plugin_manifest.objects}

    @staticmethod
    def empty() -> "RemotePluginRegistry":
        return RemotePluginRegistry(PluginManifest(modules=[], objects=[]))

    @property
    def modules(self) -> Sequence[str]:
        return self._modules

    def module_entries(self, module: str) -> Set[PluginObjectKey]:
        return {key for key in self._objects.keys() if key.package == module}

    # This differs from "modules" in that it is a list of root modules-- so if there are two entry
    # points foo.lib and foo.lib2, this will return ["foo"].
    @property
    def packages(self) -> Sequence[str]:
        return sorted({m.split(".")[0] for m in self._modules})

    def get_objects(
        self, package: Optional[str] = None, feature: Optional[PluginObjectFeature] = None
    ) -> Sequence[PluginObjectSnap]:
        return [
            entry
            for entry in self._objects.values()
            if (package is None or package == entry.key.package)
            and (feature is None or feature in entry.features)
        ]

    def get(self, key: PluginObjectKey) -> PluginObjectSnap:
        """Resolves a library object within the scope of a given component directory."""
        return self._objects[key]

    def has(self, key: PluginObjectKey) -> bool:
        return key in self._objects

    def keys(self) -> Iterable[PluginObjectKey]:
        yield from sorted(self._objects.keys(), key=lambda k: k.to_typename())

    def items(self) -> Iterable[tuple[PluginObjectKey, PluginObjectSnap]]:
        yield from self._objects.items()

    def __repr__(self) -> str:
        return f"<RemotePluginRegistry {list(self._objects.keys())}>"


def all_components_schema_from_dg_context(dg_context: "DgContext") -> Mapping[str, Any]:
    """Generate a schema for all components in the current environment, or retrieve it from the cache."""
    if dg_context.is_plugin_cache_enabled:
        cache_key = dg_context.get_cache_key("all_components_schema")
        schema = dg_context.cache.get(cache_key, dict[str, Any])
    else:
        schema = None

    if schema is None:
        if dg_context.has_cache:
            print("Component schema cache is invalidated or empty. Building cache...")  # noqa: T201
        schema_raw = dg_context.external_components_command(["list", "all-components-schema"])
        schema = json.loads(schema_raw)

    return schema


# ########################
# ##### HELPERS
# ########################

MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION = Version("1.10.12")


def _load_entry_point_components(
    dg_context: "DgContext",
) -> PluginManifest:
    if dg_context.is_plugin_cache_enabled:
        cache_key = dg_context.get_cache_key("plugin_registry_data")
        plugin_manifest = dg_context.cache.get(cache_key, PluginManifest)
    else:
        cache_key = None
        plugin_manifest = None

    if not plugin_manifest:
        if dg_context.is_plugin_cache_enabled:
            print("Plugin object cache is invalidated or empty. Building cache...")  # noqa: T201
        plugin_manifest = _fetch_plugin_manifest(dg_context, [])
        if dg_context.is_plugin_cache_enabled and cache_key:
            dg_context.cache.set(cache_key, serialize_value(plugin_manifest))
    return plugin_manifest


def _load_module_library_objects(dg_context: "DgContext", modules: Sequence[str]) -> PluginManifest:
    modules_to_fetch = set(modules)
    objects: list[PluginObjectSnap] = []
    if dg_context.is_plugin_cache_enabled:
        for module in modules:
            cache_key = dg_context.get_cache_key_for_module(module)
            plugin_objects = dg_context.cache.get(cache_key, list[PluginObjectSnap])
            if plugin_objects is not None:
                objects.extend(plugin_objects)
                modules_to_fetch.remove(module)

    if modules_to_fetch:
        if dg_context.has_cache:
            print(  # noqa: T201
                f"Plugin object cache is invalidated or empty for modules: [{modules_to_fetch}]. Building cache..."
            )
        plugin_manifest = _fetch_plugin_manifest(
            dg_context, ["--no-entry-points", *modules_to_fetch]
        )
        for module in modules_to_fetch:
            objects_for_module = [
                obj for obj in plugin_manifest.objects if obj.key.namespace == module
            ]
            objects.extend(objects_for_module)

            if dg_context.is_plugin_cache_enabled:
                cache_key = dg_context.get_cache_key_for_module(module)
                dg_context.cache.set(cache_key, serialize_value(objects_for_module))

    return PluginManifest(modules=modules, objects=objects)


# Prior to MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION, the relevant command was named
# "list library" instead of "list plugins". It also output a list[PluginObjectSnap] instead of a
# PluginManifest. This function handles normalizing the output across versions. We can compute a
# PluginManifest from the list[PluginObjectSnap], but it won't include any modules that register an
# entry point but don't expose any plugin objects.
def _fetch_plugin_manifest(context: "DgContext", args: list[str]) -> PluginManifest:
    if context.dagster_version < MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION:
        result = context.external_components_command(["list", "library", *args])
        return _plugin_objects_to_manifest(
            deserialize_value(result, as_type=list[PluginObjectSnap])
        )
    else:
        result = context.external_components_command(["list", "plugins", *args])
        result = deserialize_value(result, as_type=Union[SerializableErrorInfo, PluginManifest])
        if isinstance(result, SerializableErrorInfo):
            clean_result = remove_system_frames_from_error(
                result.cause,
                make_simple_frames_removed_hint(),
            )
            message_match = check.not_none(
                re.match(r"^\S+:\s+(Error loading entry point `(\S+?)`.*)", result.message)
            )
            header_message = message_match.group(1)
            entry_point_module = message_match.group(2)
            console = Console()
            console.print(header_message)
            console.line()
            panel = Panel(
                clean_result.to_string(),
                title=f"Entry point error ({entry_point_module})",
                expand=False,
            )
            console.print(panel)
            sys.exit(1)
        return result


def _plugin_objects_to_manifest(objects: list[PluginObjectSnap]) -> PluginManifest:
    modules = {obj.key.package for obj in objects}
    return PluginManifest(modules=sorted(modules), objects=objects)


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
