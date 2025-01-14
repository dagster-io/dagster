import os
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path


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
for component_name in list(registry.keys()):
    print(component_name)
"""


def _get_component_types_in_python_environment(python_executable: Path) -> Sequence[str]:
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(COMPONENT_PRINT_SCRIPT)
        f.flush()
        result = subprocess.run(
            [str(python_executable), f.name], capture_output=True, text=True, check=False
        )
        return result.stdout.strip().split("\n")


def _find_repo_root():
    current = Path(__file__).parent
    while not (current / ".git").exists():
        if current == Path("/"):
            raise Exception("Could not find the repository root.")
        current = current.parent
    return current


def _generate_test_component_source(number: int) -> str:
    return textwrap.dedent(f"""
    from dagster_components import Component, component_type
    @component_type(name="test_component_{number}")
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
        assert "dagster_components.pipes_subprocess_script_collection" in component_types
        assert "dagster_components.dbt_project" not in component_types
        assert "dagster_components.sling_replication_collection" not in component_types

    with _temp_venv(
        [*common_deps, "-e", f"{components_root}[dbt]", "-e", dbt_root]
    ) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster_components.pipes_subprocess_script_collection" in component_types
        assert "dagster_components.dbt_project" in component_types
        assert "dagster_components.sling_replication_collection" not in component_types

    with _temp_venv(
        [*common_deps, "-e", f"{components_root}[sling]", "-e", sling_root]
    ) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster_components.pipes_subprocess_script_collection" in component_types
        assert "dagster_components.dbt_project" not in component_types
        assert "dagster_components.sling_replication_collection" in component_types


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


def test_components_from_third_party_lib(tmpdir):
    with tmpdir.as_cwd():
        # Create test package that defines some components
        os.makedirs("dagster-foo")
        with open("dagster-foo/pyproject.toml", "w") as f:
            f.write(DAGSTER_FOO_PYPROJECT_TOML)

        os.makedirs("dagster-foo/dagster_foo/lib/sub")

        with open("dagster-foo/dagster_foo/lib/__init__.py", "w") as f:
            f.write(DAGSTER_FOO_LIB_ROOT)

        with open("dagster-foo/dagster_foo/lib/sub/__init__.py", "w") as f:
            f.write(_generate_test_component_source(2))

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
            assert "dagster_foo.test_component_1" in component_types
            assert "dagster_foo.test_component_2" in component_types
