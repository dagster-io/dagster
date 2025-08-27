import importlib
import importlib.metadata
import inspect
import sys
from collections.abc import Iterable, Sequence
from types import ModuleType

from dagster_shared.error import DagsterError, DagsterUnresolvableSymbolError
from dagster_shared.serdes.objects import EnvRegistryKey
from dagster_shared.seven import load_module_object

from dagster.components.scaffold.scaffold import has_scaffolder
from dagster.components.utils import format_error_message

PACKAGE_ENTRY_ATTR = "__dg_package_entry__"
DG_PLUGIN_ENTRY_POINT_GROUP = "dagster_dg_cli.registry_modules"

# Remove in future, in place for backcompat
OLD_DG_PLUGIN_ENTRY_POINT_GROUPS = [
    "dagster_dg.library",
    "dagster_dg.plugin",
    "dagster_dg_cli.plugin",
]


class ComponentsEntryPointLoadError(DagsterError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def get_entry_points_from_python_environment(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


def get_plugin_entry_points() -> Sequence[importlib.metadata.EntryPoint]:
    entry_points = []
    entry_points.extend(get_entry_points_from_python_environment(DG_PLUGIN_ENTRY_POINT_GROUP))
    for entry_point_group in OLD_DG_PLUGIN_ENTRY_POINT_GROUPS:
        entry_points.extend(get_entry_points_from_python_environment(entry_point_group))
    return entry_points


def discover_entry_point_package_objects() -> dict[EnvRegistryKey, object]:
    """Discover package entries registered in the Python environment via the
    `dagster_dg_cli.registry_modules` entry point group.
    """
    objects: dict[EnvRegistryKey, object] = {}

    for entry_point in get_plugin_entry_points():
        try:
            root_module = entry_point.load()
        except Exception as e:
            raise ComponentsEntryPointLoadError(
                format_error_message(f"""
                    Error loading entry point `{entry_point.value}` in group `{entry_point.group}`.
                    Please fix the error or uninstall the package that defines this entry point.
                """)
            ) from e

        if not isinstance(root_module, ModuleType):
            raise DagsterError(
                f"Invalid entry point {entry_point.name} in group {DG_PLUGIN_ENTRY_POINT_GROUP}. "
                f"Value expected to be a module, got {root_module}."
            )
        for name, obj in get_package_objects_in_module(root_module):
            key = EnvRegistryKey(name=name, namespace=entry_point.value)
            objects[key] = obj
    return objects


def discover_package_objects(modules: Sequence[str]) -> dict[EnvRegistryKey, object]:
    objects: dict[EnvRegistryKey, object] = {}
    for extra_module in modules:
        for name, obj in get_package_objects_in_module(importlib.import_module(extra_module)):
            key = EnvRegistryKey(name=name, namespace=extra_module)
            objects[key] = obj
    return objects


def get_package_objects_in_module(
    module: ModuleType,
) -> Iterable[tuple[str, object]]:
    for attr in dir(module):
        value = getattr(module, attr)
        if hasattr(value, PACKAGE_ENTRY_ATTR) and not inspect.isabstract(value):
            yield attr, value


def is_scaffoldable_object_key(key: EnvRegistryKey) -> bool:
    try:
        obj = load_module_object(key.namespace, key.name)
        return has_scaffolder(obj)
    except DagsterUnresolvableSymbolError:
        return False
