from pathlib import Path
from typing import List, Tuple, cast

from dagster_components.core.component import ComponentTypeRegistry
from dagster_components.core.component_defs_builder import (
    build_components_from_component_path,
    loading_context_for_component_path,
)

from dagster_components_tests.scope_tests.footran_component.component import FootranComponent


def test_custom_scope() -> None:
    components = build_components_from_component_path(
        path=Path(__file__).parent / "footran_component",
        registry=ComponentTypeRegistry.empty(),
        resources={},
    )

    assert len(components) == 1
    component = components[0]

    # This fails due to lack of proper module caching with the right package name
    # assert isinstance(component, FootranComponent)
    assert type(component).__name__ == "FootranComponent"
    component = cast(FootranComponent, component)

    assert component.target_address == "some_address"
    load_context = loading_context_for_component_path(
        path=Path(__file__).parent / "footran_component",
        registry=ComponentTypeRegistry.empty(),
        resources={},
    )
    assert component.required_env_vars(load_context) == {"FOOTRAN_API_KEY", "FOOTRAN_API_SECRET"}


import os


def find_package_root(file_path: str) -> Tuple[str, List[str]]:
    """Starting from the directory containing 'file_path', walk upward
    until we find a directory that is NOT a Python package
    (i.e., no __init__.py).

    Returns the absolute path of the 'package root' directory (which
    itself may have an __init__.py if it's still part of a package),
    plus the list of path components under that root.

    Example:
      If file_path = "/home/user/project/my_pkg/sub_pkg/module.py"
      and /home/user/project/my_pkg/__init__.py exists,
      and /home/user/project/__init__.py does NOT exist,
      then the package root is "/home/user/project"
      and the sub-path is ["my_pkg", "sub_pkg", "module.py"].
    """
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        raise ValueError(f"Path {file_path} is not a file.")

    dir_path = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    # We will accumulate path components in reverse, then reverse them at the end
    components = [Path(filename).stem]

    # Traverse upward while the directory contains an __init__.py,
    # meaning it is part of a package.
    while True:
        init_py = os.path.join(dir_path, "__init__.py")
        parent_dir = os.path.dirname(dir_path)

        if not os.path.isfile(init_py):
            # The current dir_path is not a python package directory
            # so break: we've found the package "root" (which might
            # itself still have an __init__.py, or might be outside any package).
            break

        # If we do have an __init__.py, then the directory is part of the package,
        # so add that directory name to our components and go one level up.
        components.append(os.path.basename(dir_path))

        # Move upward in the filesystem
        dir_path = parent_dir

        # If we reach the filesystem root, stop
        if dir_path == "/" or not dir_path:
            break

    components.reverse()  # Now it's from top-level package -> ... -> filename
    return dir_path, components


def package_name(file_path: str) -> str:
    _, components = find_package_root(file_path)
    return ".".join(components)


def test_get_full_module_name() -> None:
    comp_path = Path(__file__).parent / "footran_component" / "component.py"
    assert comp_path.exists()

    dir_path, components = find_package_root(str(comp_path))

    # import code

    # code.interact(local=locals())

    assert (
        package_name(str(comp_path))
        == "dagster_components_tests.scope_tests.footran_component.component"
    )
