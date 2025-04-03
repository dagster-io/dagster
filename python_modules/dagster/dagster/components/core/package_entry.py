import importlib
import importlib.metadata
import inspect
import sys
from collections.abc import Iterable, Sequence
from types import ModuleType

from dagster_shared.serdes.objects import PackageObjectKey

from dagster._core.errors import DagsterError
from dagster.components.utils import format_error_message

PACKAGE_ENTRY_ATTR = "__dg_package_entry__"
DG_LIBRARY_ENTRY_POINT_GROUP = "dagster_dg.library"


class ComponentsEntryPointLoadError(DagsterError):
    pass


def get_entry_points_from_python_environment(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


def discover_entry_point_package_objects() -> dict[PackageObjectKey, object]:
    """Discover package entries registered in the Python environment via the
    `dg_library` entry point group.

    `dagster-components` itself registers multiple component entry points. We call these
    "builtin" component libraries. The `dagster_components` entry point resolves to published
    component types and is loaded by default. Other entry points resolve to various sets of test
    component types. This method will only ever load one builtin package.
    """
    objects: dict[PackageObjectKey, object] = {}
    entry_points = get_entry_points_from_python_environment(DG_LIBRARY_ENTRY_POINT_GROUP)

    for entry_point in entry_points:
        try:
            root_module = entry_point.load()
        except Exception as e:
            raise ComponentsEntryPointLoadError(
                format_error_message(f"""
                    Error loading entry point `{entry_point.name}` in group `{DG_LIBRARY_ENTRY_POINT_GROUP}`.
                    Please fix the error or uninstall the package that defines this entry point.
                """)
            ) from e

        if not isinstance(root_module, ModuleType):
            raise DagsterError(
                f"Invalid entry point {entry_point.name} in group {DG_LIBRARY_ENTRY_POINT_GROUP}. "
                f"Value expected to be a module, got {root_module}."
            )
        for name, obj in get_package_objects_in_module(root_module):
            key = PackageObjectKey(name=name, namespace=entry_point.value)
            objects[key] = obj
    return objects


def discover_package_objects(modules: Sequence[str]) -> dict[PackageObjectKey, object]:
    objects: dict[PackageObjectKey, object] = {}
    for extra_module in modules:
        for name, obj in get_package_objects_in_module(importlib.import_module(extra_module)):
            key = PackageObjectKey(name=name, namespace=extra_module)
            objects[key] = obj
    return objects


def get_package_objects_in_module(
    module: ModuleType,
) -> Iterable[tuple[str, object]]:
    for attr in dir(module):
        value = getattr(module, attr)
        if hasattr(value, PACKAGE_ENTRY_ATTR) and not inspect.isabstract(value):
            yield attr, value


def load_package_object(key: PackageObjectKey) -> object:
    module_name, attr = key.namespace, key.name
    try:
        module = importlib.import_module(module_name)
        if not hasattr(module, attr):
            raise DagsterError(f"Module `{module_name}` has no attribute `{attr}`.")
        return getattr(module, attr)
    except ModuleNotFoundError as e:
        raise DagsterError(f"Module `{module_name}` not found.") from e
    except ImportError as e:
        raise DagsterError(f"Error loading module `{module_name}`.") from e
