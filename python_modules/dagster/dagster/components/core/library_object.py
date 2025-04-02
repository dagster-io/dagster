import importlib
import importlib.metadata
import inspect
import sys
from collections.abc import Iterable, Sequence
from types import ModuleType

from dagster_shared.serdes.objects import LibraryObjectKey

from dagster._core.errors import DagsterError
from dagster.components.utils import format_error_message

LIBRARY_OBJECT_ATTR = "__dg_library_object__"
DG_LIBRARY_ENTRY_POINT_GROUP = "dagster_dg.library"


class ComponentsEntryPointLoadError(DagsterError):
    pass


def get_entry_points_from_python_environment(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


def discover_entry_point_library_objects() -> dict[LibraryObjectKey, object]:
    """Discover library objects registered in the Python environment via the
    `dg_library` entry point group.

    `dagster-components` itself registers multiple component entry points. We call these
    "builtin" component libraries. The `dagster_components` entry point resolves to published
    component types and is loaded by default. Other entry points resolve to various sets of test
    component types. This method will only ever load one builtin component library.
    """
    objects: dict[LibraryObjectKey, object] = {}
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
        for name, obj in get_library_objects_in_module(root_module):
            key = LibraryObjectKey(name=name, namespace=entry_point.value)
            objects[key] = obj
    return objects


def discover_library_objects(modules: Sequence[str]) -> dict[LibraryObjectKey, object]:
    objects: dict[LibraryObjectKey, object] = {}
    for extra_module in modules:
        for name, obj in get_library_objects_in_module(importlib.import_module(extra_module)):
            key = LibraryObjectKey(name=name, namespace=extra_module)
            objects[key] = obj
    return objects


def get_library_objects_in_module(
    module: ModuleType,
) -> Iterable[tuple[str, object]]:
    for attr in dir(module):
        value = getattr(module, attr)
        if hasattr(value, LIBRARY_OBJECT_ATTR) and not inspect.isabstract(value):
            yield attr, value


def load_library_object(key: LibraryObjectKey) -> object:
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
