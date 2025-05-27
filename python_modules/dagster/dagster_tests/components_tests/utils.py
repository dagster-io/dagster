import contextlib
import random
import shutil
import tempfile
import textwrap
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Any, Iterable, Optional, TypeVar  # noqa: UP035

import tomlkit
from click.testing import Result
from dagster._utils import alter_sys_path, pushd
from dagster.components import Component, ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent, get_component
from dagster.components.utils import ensure_loadable_path

T = TypeVar("T")
T_Component = TypeVar("T_Component", bound=Component)


def generate_component_lib_pyproject_toml(name: str, is_project: bool = False) -> str:
    pkg_name = name.replace("-", "_")
    base = textwrap.dedent(f"""
        [build-system]
        requires = ["setuptools", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{name}"
        version = "0.1.0"
        dependencies = [
            "dagster",
        ]

        [project.entry-points]
        "dagster_dg.plugin" = {{ {pkg_name} = "{pkg_name}.lib" }}
    """)
    if is_project:
        return base + textwrap.dedent(f"""
        [tool.dg]
        directory_type = "project"

        [tool.dg.project]
        root_module = "{pkg_name}"
        code_location_name = "{pkg_name}"
        """)
    else:
        return base


@contextmanager
def temp_code_location_bar() -> Iterator[None]:
    with TemporaryDirectory() as tmpdir, pushd(tmpdir):
        Path("bar/bar/lib").mkdir(parents=True)
        Path("bar/bar/components").mkdir(parents=True)
        with open("bar/pyproject.toml", "w") as f:
            f.write(generate_component_lib_pyproject_toml("bar", is_project=True))
        Path("bar/bar/__init__.py").touch()
        Path("bar/bar/definitions.py").touch()
        Path("bar/bar/lib/__init__.py").touch()

        with pushd("bar"):
            yield


def _setup_component_in_folder(
    src_path: str, dst_path: str, local_component_defn_to_inject: Optional[Path]
) -> None:
    origin_path = Path(__file__).parent / "integration_tests" / "integration_test_defs" / src_path

    shutil.copytree(origin_path, dst_path, dirs_exist_ok=True)
    if local_component_defn_to_inject:
        shutil.copy(local_component_defn_to_inject, Path(dst_path) / "__init__.py")


@contextlib.contextmanager
def inject_component(
    src_path: str, local_component_defn_to_inject: Optional[Path]
) -> Iterator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_component_in_folder(src_path, tmpdir, local_component_defn_to_inject)
        yield tmpdir


@contextlib.contextmanager
def create_project_from_components(
    *src_paths: str, local_component_defn_to_inject: Optional[Path] = None
) -> Iterator[tuple[Path, str]]:
    """Scaffolds a project with the given components in a temporary directory,
    injecting the provided local component defn into each component's __init__.py.
    """
    location_name = f"my_location_{random.randint(0, 2**32 - 1)}"

    # Using mkdtemp instead of TemporaryDirectory so that the directory is accessible
    # from launched procsses (such as duckdb)
    tmpdir = tempfile.mkdtemp()
    try:
        project_root = Path(tmpdir) / location_name
        project_root.mkdir()

        python_module_root = project_root / location_name
        python_module_root.mkdir()
        (python_module_root / "__init__.py").touch()

        defs_dir = python_module_root / "defs"
        defs_dir.mkdir()
        (defs_dir / "__init__.py").touch()

        with alter_sys_path(to_add=[str(project_root)], to_remove=[]):
            with open(project_root / "pyproject.toml", "w") as f:
                f.write(generate_component_lib_pyproject_toml(location_name, is_project=True))

            for src_path in src_paths:
                component_name = src_path.split("/")[-1]

                components_dir = defs_dir / component_name
                components_dir.mkdir()

                _setup_component_in_folder(
                    src_path=src_path,
                    dst_path=str(components_dir),
                    local_component_defn_to_inject=local_component_defn_to_inject,
                )

            with ensure_loadable_path(project_root):
                yield project_root, location_name
    finally:
        shutil.rmtree(tmpdir)


# ########################
# ##### CLI RUNNER
# ########################


def assert_runner_result(result: Result, exit_0: bool = True) -> None:
    try:
        assert result.exit_code == 0 if exit_0 else result.exit_code != 0
    except AssertionError:
        if result.output:
            print(result.output)  # noqa: T201
        if result.exc_info:
            print_exception_info(result.exc_info)
        raise


def print_exception_info(
    exc_info: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    """Prints a nicely formatted traceback for the current exception."""
    exc_type, exc_value, exc_traceback = exc_info
    print("Exception Traceback (most recent call last):")  # noqa: T201
    formatted_traceback = "".join(traceback.format_tb(exc_traceback))
    print(formatted_traceback)  # noqa: T201
    print(f"{exc_type.__name__}: {exc_value}")  # noqa: T201


# ########################
# ##### TOML MANIPULATION
# ########################

# Copied from dagster-dg


@contextmanager
def modify_toml(path: Path) -> Iterator[tomlkit.TOMLDocument]:
    with open(path) as f:
        toml = tomlkit.parse(f.read())
    yield toml
    with open(path, "w") as f:
        f.write(tomlkit.dumps(toml))


def get_toml_value(doc: tomlkit.TOMLDocument, path: Iterable[str], expected_type: type[T]) -> T:
    """Given a tomlkit-parsed document/table (`doc`),retrieve the nested value at `path` and ensure
    it is of type `expected_type`. Returns the value if so, or raises a KeyError / TypeError if not.
    """
    current: Any = doc
    for key in path:
        # If current is not a table/dict or doesn't have the key, error out
        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"Key '{key}' not found in path: {'.'.join(path)}")
        current = current[key]

    # Finally, ensure the found value is of the expected type
    if not isinstance(current, expected_type):
        raise TypeError(
            f"Expected '{'.'.join(path)}' to be {expected_type.__name__}, "
            f"but got {type(current).__name__} instead."
        )
    return current


def set_toml_value(doc: tomlkit.TOMLDocument, path: Iterable[str], value: object) -> None:
    """Given a tomlkit-parsed document/table (`doc`),set a nested value at `path` to `value`. Raises
    an error if the leading keys do not already lead to a dictionary.
    """
    path_list = list(path)
    inner_dict = get_toml_value(doc, path_list[:-1], dict)
    inner_dict[path_list[-1]] = value


def get_underlying_component(context: ComponentLoadContext) -> Optional[Component]:
    """Loads a component from the given context, resolving the underlying component if
    it is a CompositeYamlComponent.
    """
    component = get_component(context)
    if isinstance(component, CompositeYamlComponent):
        assert len(component.components) == 1
        return component.components[0]
    return component
