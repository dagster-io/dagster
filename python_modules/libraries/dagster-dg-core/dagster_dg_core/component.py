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
from dagster_shared.serdes.objects import EnvRegistryKey, EnvRegistryObjectSnap
from dagster_shared.serdes.objects.package_entry import (
    EnvRegistryManifest,
    EnvRegistryObjectFeature,
)
from packaging.version import Version

from dagster_dg_core.utils.warnings import emit_warning

if TYPE_CHECKING:
    from dagster_dg_core.context import DgContext


class EnvRegistry:
    @staticmethod
    def from_dg_context(
        dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "EnvRegistry":
        """Fetches the set of available registry objects. The default set includes everything
        discovered under the "dagster_dg_cli.registry_modules" entry point group in the target environment. If
        `extra_modules` is provided, these will also be searched for component types.
        """
        if dg_context.config.cli.use_component_modules:
            plugin_manifest = _load_module_registry_objects(
                dg_context, dg_context.config.cli.use_component_modules
            )
        else:
            plugin_manifest = _load_entry_point_registry_objects(dg_context)

        if extra_modules:
            deduped_extra_modules = set(extra_modules).difference(plugin_manifest.modules)
            plugin_manifest = plugin_manifest.merge(
                _load_module_registry_objects(dg_context, deduped_extra_modules)
            )

        # Only load project plugin modules if there is no entry point
        if dg_context.is_project and not dg_context.has_registry_module_entry_point:
            if dg_context.project_registry_modules:
                deduped_project_modules = set(dg_context.project_registry_modules).difference(
                    plugin_manifest.modules
                )
                plugin_manifest = plugin_manifest.merge(
                    _load_module_registry_objects(dg_context, deduped_project_modules)
                )

        if (
            dg_context.has_registry_module_entry_point
            and not dg_context.config.cli.use_component_modules
            and dg_context.default_registry_root_module_name not in plugin_manifest.modules
        ):
            emit_warning(
                "missing_dg_plugin_module_in_manifest",
                f"""
                Your package defines a `dagster_dg_cli.registry_modules` entry point, but this module was not
                found in the plugin manifest for the current environment. This means either that
                your project is not installed in the current environment, or that the entry point
                metadata was added after your module was installed. Python entry points are
                registered at package install time. Please reinstall your package into the current
                environment to ensure the entry point is registered.

                Entry point module: `{dg_context.default_registry_root_module_name}`
                """,
                suppress_warnings=dg_context.config.cli.suppress_warnings,
            )

        return EnvRegistry(plugin_manifest)

    def __init__(self, plugin_manifest: EnvRegistryManifest):
        self._plugin_manifest = plugin_manifest
        self._object_lookup = {key: obj for obj in plugin_manifest.objects for key in obj.all_keys}

    @staticmethod
    def empty() -> "EnvRegistry":
        return EnvRegistry(EnvRegistryManifest(modules=[], objects=[]))

    @property
    def modules(self) -> Sequence[str]:
        return self._plugin_manifest.modules

    def module_entries(self, module: str) -> Set[EnvRegistryKey]:
        return {obj.key for obj in self._plugin_manifest.objects if obj.key.package == module}

    # This differs from "modules" in that it is a list of root modules-- so if there are two entry
    # points foo.lib and foo.lib2, this will return ["foo"].
    @property
    def packages(self) -> Sequence[str]:
        return sorted({m.split(".")[0] for m in self._plugin_manifest.modules})

    def get_objects(
        self,
        package: Optional[str] = None,
        feature: Optional[EnvRegistryObjectFeature] = None,
    ) -> Sequence[EnvRegistryObjectSnap]:
        return [
            entry
            for entry in self._plugin_manifest.objects
            if (package is None or package == entry.key.package)
            and (feature is None or feature in entry.features)
        ]

    def get(self, key: EnvRegistryKey) -> EnvRegistryObjectSnap:
        """Resolves a library object within the scope of a given component directory."""
        return self._object_lookup[key]

    def has(self, key: EnvRegistryKey) -> bool:
        return key in self._object_lookup

    def keys(self) -> Iterable[EnvRegistryKey]:
        yield from sorted(
            (obj.key for obj in self._plugin_manifest.objects), key=lambda k: k.to_typename()
        )

    def items(self) -> Iterable[tuple[EnvRegistryKey, EnvRegistryObjectSnap]]:
        yield from ((obj.key, obj) for obj in self._plugin_manifest.objects)

    def __repr__(self) -> str:
        return f"<EnvRegistry {list(self.keys())}>"


def all_components_schema_from_dg_context(dg_context: "DgContext") -> Mapping[str, Any]:
    """Generate a schema for all components in the current environment."""
    from dagster.components.list import list_all_components_schema

    return list_all_components_schema(entry_points=True, extra_modules=())


# ########################
# ##### HELPERS
# ########################

MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION = Version("1.10.12")


def _load_entry_point_registry_objects(
    dg_context: "DgContext",
) -> EnvRegistryManifest:
    return _fetch_plugin_manifest(entry_points=True, extra_modules=[])


def _load_module_registry_objects(
    dg_context: "DgContext", modules: Iterable[str]
) -> EnvRegistryManifest:
    modules_to_fetch = set(modules)
    objects: list[EnvRegistryObjectSnap] = []

    if modules_to_fetch:
        plugin_manifest = _fetch_plugin_manifest(
            entry_points=False, extra_modules=list(modules_to_fetch)
        )
        for module in modules_to_fetch:
            objects_for_module = [
                obj for obj in plugin_manifest.objects if obj.key.namespace == module
            ]
            objects.extend(objects_for_module)

    return EnvRegistryManifest(modules=list(modules), objects=objects)


# Prior to MIN_DAGSTER_COMPONENTS_LIST_PLUGINS_VERSION, the relevant command was named "list
# library" instead of "list plugins". It also output a list[EnvRegistryObjectSnap] instead
# of a EnvRegistryManifest. This function handles normalizing the output across versions. We
# can compute a EnvRegistryManifest from the list[EnvRegistryObjectSnap], but it
# won't include any modules that register an entry point but don't expose any plugin objects.
def _fetch_plugin_manifest(entry_points: bool, extra_modules: Sequence[str]) -> EnvRegistryManifest:
    from dagster.components.list import list_plugins
    from rich.console import Console
    from rich.panel import Panel

    result = list_plugins(entry_points=entry_points, extra_modules=extra_modules)

    if isinstance(result, SerializableErrorInfo):
        clean_result = remove_system_frames_from_error(
            result.cause if result.cause else result,
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


def get_specified_env_var_deps(component_data: Mapping[str, Any]) -> set[str]:
    if not component_data.get("requirements") or "env" not in component_data["requirements"]:
        return set()
    return set(component_data["requirements"]["env"])


env_var_regex = re.compile(r"\{\{\s*env\(\s*['\"]([^'\"]+)['\"]\)\s*\}\}")
env_var_regex_dot_notation = re.compile(r"\{\{\s*env\.([^'\"\s]+)\s*\}\}")


def get_used_env_vars(data_structure: Union[Mapping[str, Any], Sequence[Any], Any]) -> set[str]:
    if isinstance(data_structure, Mapping):
        return set.union(set(), *(get_used_env_vars(value) for value in data_structure.values()))
    elif isinstance(data_structure, str):
        raw_result = set(env_var_regex.findall(data_structure)).union(
            set(env_var_regex_dot_notation.findall(data_structure))
        )
        return {var.strip() for var in raw_result}
    elif isinstance(data_structure, Sequence):
        return set.union(set(), *(get_used_env_vars(item) for item in data_structure))
    else:
        return set()
