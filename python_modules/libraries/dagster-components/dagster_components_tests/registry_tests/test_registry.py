import json
import os
import subprocess
import tempfile
import textwrap
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

from dagster._utils import pushd
from dagster_components.utils import ensure_dagster_components_tests_import
from dagster_dg.utils import get_venv_executable

ensure_dagster_components_tests_import()

from dagster_components_tests.utils import modify_toml, set_toml_value


@contextmanager
def _temp_venv(install_args: Sequence[str]) -> Iterator[Path]:
    # Create venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / ".venv"
        subprocess.check_call(["uv", "venv", str(venv_dir)])
        subprocess.check_call(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(get_venv_executable(venv_dir, "python")),
                *install_args,
            ]
        )
        yield venv_dir


COMPONENT_PRINT_SCRIPT = """
from dagster_components import ComponentTypeRegistry

registry = ComponentTypeRegistry.from_entry_point_discovery()
for component_key in list(registry.keys()):
    print(component_key.to_typename())
"""


def _get_component_print_script_result(venv_root: Path) -> subprocess.CompletedProcess:
    assert venv_root.exists()
    dagster_components_path = get_venv_executable(venv_root, "dagster-components")
    assert dagster_components_path.exists()
    result = subprocess.run(
        [str(dagster_components_path), "list", "component-types"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def _get_component_types_in_python_environment(venv_root: Path) -> Sequence[str]:
    result = _get_component_print_script_result(venv_root)
    return list(json.loads(result.stdout).keys())


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

            with _temp_venv(deps) as venv_root:
                yield venv_root


def test_components_from_third_party_lib():
    with isolated_venv_with_component_lib_dagster_foo() as venv_root:
        component_types = _get_component_types_in_python_environment(venv_root)
        assert "test_component_1@dagster_foo" in component_types
        assert "test_component_2@dagster_foo" in component_types


def test_bad_entry_point_error_message():
    # Modify the entry point to point to a non-existent module. This has to be done before the
    # package is installed, which is why we use a pre-install hook.
    def pre_install_hook():
        with modify_toml(Path("dagster-foo/pyproject.toml")) as toml:
            set_toml_value(
                toml,
                ("project", "entry-points", "dagster.components", "dagster_foo"),
                "fake.module",
            )

    with isolated_venv_with_component_lib_dagster_foo(pre_install_hook) as venv_root:
        result = _get_component_print_script_result(venv_root)
        assert (
            "Error loading entry point `dagster_foo` in group `dagster.components`" in result.stderr
        )
        assert result.returncode != 0
