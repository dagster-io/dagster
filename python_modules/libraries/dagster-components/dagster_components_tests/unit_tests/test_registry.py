import os
import subprocess
import sys
from pathlib import Path

from dagster_components import ComponentRegistry


def test_components_from_dagster():
    registry = ComponentRegistry.from_entry_point_discovery()
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

# Our pyproject.toml installs local dagster components
PYPROJECT_TOML = f"""
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

[tool.uv.sources]
dagster = {{ path = "{repo_root}/python_modules/dagster" }}
dagster-pipes = {{ path = "{repo_root}/python_modules/dagster-pipes" }}
dagster-components = {{ path = "{repo_root}/python_modules/libraries/dagster-components" }}
dagster-dbt = {{ path = "{repo_root}/python_modules/libraries/dagster-dbt" }}
dagster-embedded-elt = {{ path = "{repo_root}/python_modules/libraries/dagster-embedded-elt" }}

[project.entry-points]
"dagster.components" = {{ dagster_foo = "dagster_foo.lib"}}
"""

TEST_COMPONENT_1 = """
from dagster_components import Component, component

@component(name="test_component_1")
class TestComponent1(Component):
    pass
"""

TEST_COMPONENT_2 = """
from dagster_components import Component, component

@component(name="test_component_2")
class TestComponent2(Component):
    pass
"""

COMPONENT_PRINT_SCRIPT = """
from dagster_components import ComponentRegistry

registry = ComponentRegistry.from_entry_point_discovery()
for component_name in list(registry.keys()):
    print(component_name)
"""


def test_components_from_third_party_lib(tmpdir):
    with tmpdir.as_cwd():
        # Create test package that defines some components
        os.makedirs("dagster-foo")
        with open("dagster-foo/pyproject.toml", "w") as f:
            f.write(PYPROJECT_TOML)

        os.makedirs("dagster-foo/dagster_foo/lib/sub")

        with open("dagster-foo/dagster_foo/lib/__init__.py", "w") as f:
            f.write(TEST_COMPONENT_1)

        with open("dagster-foo/dagster_foo/lib/sub/__init__.py", "w") as f:
            f.write(TEST_COMPONENT_2)

        # Create venv
        venv_dir = Path(".venv")
        subprocess.check_call(["uv", "venv", str(venv_dir)])
        python_executable = (
            venv_dir
            / ("Scripts" if sys.platform == "win32" else "bin")
            / ("python.exe" if sys.platform == "win32" else "python")
        )

        # Script to print components
        with open("print_components.py", "w") as f:
            f.write(COMPONENT_PRINT_SCRIPT)

        # subprocess.check_call([pip_executable, "install", "-e", "dagster-foo"])
        subprocess.check_call(
            ["uv", "pip", "install", "--python", str(python_executable), "-e", "dagster-foo"]
        )
        result = subprocess.run(
            [python_executable, "print_components.py"], capture_output=True, text=True, check=False
        )
        assert "dagster_foo.test_component_1" in result.stdout
        assert "dagster_foo.test_component_2" in result.stdout
