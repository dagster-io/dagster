import os
import subprocess
import sys
import tempfile
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from dagster_components import ComponentRegistry


def test_components_from_dagster():
    registry = ComponentRegistry.from_python_environment()
    assert registry.has("dagster_components.dbt_project")
    assert registry.has("dagster_components.sling_replication")
    assert registry.has("dagster_components.pipes_subprocess_script_collection")


def _find_repo_root():
    current = Path(__file__).parent
    while not (current / ".git").exists():
        if current == Path("/"):
            raise Exception("Could not find the repository root.")
        current = current.parent
    return current


repo_root = _find_repo_root()

# ########################
# ##### DAGSTER FOO TEST PACKAGE
# ########################

# Our pyproject.toml installs local dagster components
DAGSTER_FOO_PYPROJECT_TOML = f"""
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dagster-foo"
version = "0.1.0"
description = "A simple example package"
authors = [
    {{ name = "Your Name", email = "your.email@example.com" }}
]
dependencies = [
    "dagster",
    "dagster-components",
    "dagster-dbt",
    "dagster-embedded-elt",
]

[project.optional-dependencies]
bar = ["dagster-bar"]

[tool.uv.sources]
dagster = {{ path = "{repo_root}/python_modules/dagster" }}
dagster-pipes = {{ path = "{repo_root}/python_modules/dagster-pipes" }}
dagster-components = {{ path = "{repo_root}/python_modules/libraries/dagster-components" }}
dagster-dbt = {{ path = "{repo_root}/python_modules/libraries/dagster-dbt" }}
dagster-embedded-elt = {{ path = "{repo_root}/python_modules/libraries/dagster-embedded-elt" }}

[project.entry-points."dagster.components"]
"dagster_foo" = "dagster_foo.lib"
"dagster_foo.__extras__.bar" = "dagster_foo.lib.__extras__.bar"
"""


def _generate_test_component_source(number: int) -> str:
    return textwrap.dedent(f"""
    from dagster_components import Component, component

    @component(name="test_component_{number}")
    class TestComponent{number}(Component):
        pass
    """)


COMPONENT_PRINT_SCRIPT = """
from dagster_components import ComponentRegistry

registry = ComponentRegistry.from_python_environment()
for component_name in list(registry.keys()):
    print(component_name)
"""


@contextmanager
def temp_package_dagster_foo(tmpdir: Any) -> Iterator[str]:
    with tmpdir.as_cwd():
        # Create test package that defines some components
        os.makedirs("dagster-foo")
        with open("dagster-foo/pyproject.toml", "w") as f:
            f.write(DAGSTER_FOO_PYPROJECT_TOML)

        os.makedirs("dagster-foo/dagster_foo/lib/sub")

        with open("dagster-foo/dagster_foo/lib/__init__.py", "w") as f:
            f.write(_generate_test_component_source(1))

        with open("dagster-foo/dagster_foo/lib/sub/__init__.py", "w") as f:
            f.write(_generate_test_component_source(2))

        os.makedirs("dagster-foo/dagster_foo/lib/__extras__/bar/sub")

        with open("dagster-foo/dagster_foo/lib/__extras__/bar/__init__.py", "w") as f:
            f.write(_generate_test_component_source(3))

        with open("dagster-foo/dagster_foo/lib/__extras__/bar/sub/__init__.py", "w") as f:
            f.write(_generate_test_component_source(4))

        yield "dagster-foo"


# ########################
# ##### DAGSTER BAR TEST PACKAGE
# ########################

DAGSTER_BAR_PYPROJECT_TOML = """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dagster-bar"
version = "0.1.0"
"""


@contextmanager
def temp_package_dagster_bar(tmpdir: Any) -> Iterator[str]:
    with tmpdir.as_cwd():
        os.makedirs("dagster-bar/dagster_bar")
        with open("dagster-bar/pyproject.toml", "w") as f:
            f.write(DAGSTER_BAR_PYPROJECT_TOML)

        Path("dagster-bar/dagster_bar/__init__.py").touch()

        yield "dagster-bar"


# ########################
# ##### VENV
# ########################


@contextmanager
def temp_venv() -> Iterator[Path]:
    # Create venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / ".venv"
        subprocess.check_call(["uv", "venv", str(venv_dir)])
        python_executable = (
            venv_dir
            / ("Scripts" if sys.platform == "win32" else "bin")
            / ("python.exe" if sys.platform == "win32" else "python")
        )
        yield python_executable


# ########################


def test_components_from_third_party_lib(tmpdir):
    with (
        temp_package_dagster_foo(tmpdir) as package_path_foo,
        temp_package_dagster_bar(tmpdir) as package_path_bar,
    ):
        # Create venv

        # Install dagster-foo without the bar extra
        with temp_venv() as venv_python:
            # Script to print components
            with open("print_components.py", "w") as f:
                f.write(COMPONENT_PRINT_SCRIPT)

            # subprocess.check_call([pip_executable, "install", "-e", "dagster-foo"])
            subprocess.check_call(
                ["uv", "pip", "install", "--python", str(venv_python), "-e", package_path_foo]
            )
            result = subprocess.run(
                [venv_python, "print_components.py"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert "dagster_foo.test_component_1" in result.stdout
            assert "dagster_foo.test_component_2" in result.stdout
            assert "dagster_foo.test_component_3" not in result.stdout
            assert "dagster_foo.test_component_4" not in result.stdout

        # Now with the bar extra
        with temp_venv() as venv_python:
            # Script to print components
            with open("print_components.py", "w") as f:
                f.write(COMPONENT_PRINT_SCRIPT)

            # subprocess.check_call([pip_executable, "install", "-e", "dagster-foo"])
            subprocess.check_call(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(venv_python),
                    "-e",
                    f"{package_path_foo}[bar]",
                    "-e",
                    package_path_bar,
                ]
            )
            result = subprocess.run(
                [venv_python, "print_components.py"], capture_output=True, text=True, check=False
            )
            assert "dagster_foo.test_component_1" in result.stdout
            assert "dagster_foo.test_component_2" in result.stdout
            assert "dagster_foo.test_component_3" in result.stdout
            assert "dagster_foo.test_component_4" in result.stdout
