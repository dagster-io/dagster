import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from dagster._core.errors import DagsterError

CLI_BUILTIN_COMPONENT_LIB_KEY = "builtin_component_lib"


def ensure_dagster_components_tests_import() -> None:
    from dagster_components import __file__ as dagster_components_init_py

    dagster_components_package_root = (Path(dagster_components_init_py) / ".." / "..").resolve()
    assert (
        dagster_components_package_root / "dagster_components_tests"
    ).exists(), "Could not find dagster_components_tests where expected"
    sys.path.append(dagster_components_package_root.as_posix())


# Temporarily places a path at the front of sys.path, ensuring that any modules in that path are
# importable.
@contextmanager
def ensure_loadable_path(path: Path) -> Iterator[None]:
    orig_path = sys.path.copy()
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path = orig_path


def get_path_for_package(package_name: str) -> str:
    spec = importlib.util.find_spec(package_name)
    if not spec:
        raise DagsterError(f"Cannot find package: {package_name}")
    # file_path = spec.origin
    submodule_search_locations = spec.submodule_search_locations
    if not submodule_search_locations:
        raise DagsterError(f"Package does not have any locations for submodules: {package_name}")
    return submodule_search_locations[0]
