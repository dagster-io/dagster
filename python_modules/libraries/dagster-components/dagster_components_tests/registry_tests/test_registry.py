import os
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional

import tomli
import tomli_w
from dagster._utils import pushd

from dagster_dg.component import GlobalComponentKey


@contextmanager
def _temp_venv(install_args: Sequence[str]) -> Iterator[Path]:
    # Create venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / ".venv"
        subprocess.check_call(["uv", "venv", str(venv_dir)])
        python_executable = (
            venv_dir
            / ("Scripts" if sys.platform == "win32" else "bin")
            / ("python.exe" if sys.platform == "win32" else "python")
        )
        subprocess.check_call(
            ["uv", "pip", "install", "--python", str(python_executable), *install_args]
        )
        yield python_executable


COMPONENT_PRINT_SCRIPT = """
from dagster_components import ComponentTypeRegistry

registry = ComponentTypeRegistry.from_entry_point_discovery()
for component_key in list(registry.keys()):
    print(component_key.to_typename())
"""


def _get_component_print_script_output(python_executable: Path) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(COMPONENT_PRINT_SCRIPT)
        f.flush()
        result = subprocess.run(
            [str(python_executable), f.name], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()


def _get_component_types_in_python_environment(python_executable: Path) -> Sequence[str]:
    return _get_component_print_script_output(python_executable).split("\n")


def _find_repo_root():
    current = Path(__file__).parent
    while not (current / ".git").exists():
        if current == Path("/"):
            raise Exception("Could not find the repository root.")
        current = current.parent
    return current


def _generate_test_component_source(number: int) -> str:
    return textwrap.dedent(f"""
    from dagster_components import Component, registered_component_type
    @registered_component_type(name="test_component_{number}")
    class TestComponent{number}(Component):
        pass
    """)


_repo_root = _find_repo_root()


def _get_editable_package_root(pkg_name: str) -> str:
    possible_locations = [
        _repo_root / "python_modules" / pkg_name,
        _repo_root / "python_modules" / "libraries" / pkg_name,
    ]
    return next(str(loc) for loc in possible_locations if loc.exists())


# ########################
# ##### TESTS
# ########################


def test_components_from_dagster():
    common_deps: list[str] = []
    for pkg_name in ["dagster", "dagster-pipes"]:
        common_deps.extend(["-e", _get_editable_package_root(pkg_name)])

    components_root = _get_editable_package_root("dagster-components")
    dbt_root = _get_editable_package_root("dagster-dbt")
    sling_root = _get_editable_package_root("dagster-sling")

    # No extras
    with _temp_venv([*common_deps, "-e", components_root]) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "pipes_subprocess_script_collection@dagster_components" in component_types
        assert "dbt_project@dagster_components" not in component_types
        assert "sling_replication_collection@dagster_components" not in component_types

    with _temp_venv(
        [*common_deps, "-e", f"{components_root}[dbt]", "-e", dbt_root]
    ) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "pipes_subprocess_script_collection@dagster_components" in component_types
        assert "dbt_project@dagster_components" in component_types
        assert "sling_replication_collection@dagster_components" not in component_types

    with _temp_venv(
        [*common_deps, "-e", f"{components_root}[sling]", "-e", sling_root]
    ) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "pipes_subprocess_script_collection@dagster_components" in component_types
        assert "dbt_project@dagster_components" not in component_types
        assert "sling_replication_collection@dagster_components" in component_types


def test_all_dagster_components_have_defined_summary():
    from dagster_components import ComponentTypeRegistry

    registry = ComponentTypeRegistry.from_entry_point_discovery()
    for component_name, component_type in registry.items():
        assert component_type.get_metadata()[
            "summary"
        ], f"Component {component_name} has no summary defined"


# Our pyproject.toml installs local dagster components
DAGSTER_FOO_PYPROJECT_TOML = """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dagster-foo"
version = "0.1.0"
description = "A simple example package"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
dependencies = [
    "dagster-components",
]

[project.entry-points]
"dagster.components" = { dagster_foo = "dagster_foo.lib"}
"""

DAGSTER_FOO_LIB_ROOT = f"""
{_generate_test_component_source(1)}

from dagster_foo.lib.sub import TestComponent2
"""


@contextmanager
def isolated_venv_with_component_lib_dagster_foo(
    pre_install_hook: Optional[Callable[[], None]] = None,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        with pushd(tmpdir):
            # Create test package that defines some components
            os.makedirs("dagster-foo")
            with open("dagster-foo/pyproject.toml", "w") as f:
                f.write(DAGSTER_FOO_PYPROJECT_TOML)

            os.makedirs("dagster-foo/dagster_foo/lib/sub")

            with open("dagster-foo/dagster_foo/lib/__init__.py", "w") as f:
                f.write(DAGSTER_FOO_LIB_ROOT)

            with open("dagster-foo/dagster_foo/lib/sub/__init__.py", "w") as f:
                f.write(_generate_test_component_source(2))

            if pre_install_hook:
                pre_install_hook()

            # Need pipes because dependency of dagster
            deps = [
                "-e",
                _get_editable_package_root("dagster"),
                "-e",
                _get_editable_package_root("dagster-components"),
                "-e",
                _get_editable_package_root("dagster-pipes"),
                "-e",
                "dagster-foo",
            ]

            with _temp_venv(deps) as python_executable:
                component_types = _get_component_types_in_python_environment(python_executable)
                assert (
                    GlobalComponentKey(name="test_component_1", namespace="dagster_foo").to_typename()
                    in component_types
                )
                assert (
                    GlobalComponentKey(name="test_component_2", namespace="dagster_foo").to_typename()
                    in component_types
                )
                yield python_executable


@contextmanager
def modify_toml(path: Path) -> Iterator[dict[str, Any]]:
    toml = tomli.loads(path.read_text())
    yield toml
    path.write_text(tomli_w.dumps(toml))


def test_components_from_third_party_lib():
    with isolated_venv_with_component_lib_dagster_foo() as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster_foo.test_component_1" in component_types
        assert "dagster_foo.test_component_2" in component_types


# def test_entry_point_null_reference():
#
#     # Modify the entry point to point to a non-existent module
#     def pre_install_hook():
#         with modify_toml(Path("dagster-foo/pyproject.toml")) as toml:
#             toml["project"]["entry-points"]["dagster.components"]["dagster_foo"] = "fake.module"
#
#     with isolated_venv_with_component_lib_dagster_foo(pre_install_hook) as python_executable:
#         script_output = _get_component_print_script_output(python_executable)
#         # assert
#         component_types = _get_component_types_in_python_environment(python_executable)
#         assert "dagster_foo.test_component_1" in component_types
#         assert "dagster_foo.test_component_2" in component_types
