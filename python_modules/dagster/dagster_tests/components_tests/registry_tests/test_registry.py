import json
import os
import re
import subprocess
import tempfile
import textwrap
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import dagster as dg
import pytest
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import pushd
from dagster.components.core.package_entry import (
    DG_PLUGIN_ENTRY_POINT_GROUP,
    OLD_DG_PLUGIN_ENTRY_POINT_GROUPS,
    discover_entry_point_package_objects,
)
from dagster.components.core.snapshot import get_package_entry_snap
from dagster_dg_core.utils import get_venv_executable
from dagster_shared import seven
from dagster_shared.serdes.objects import EnvRegistryKey

ensure_dagster_tests_import()

from dagster_tests.components_tests.utils import modify_toml, set_toml_value


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


def _get_component_print_script_result(venv_root: Path) -> subprocess.CompletedProcess:
    assert venv_root.exists()
    dagster_components_path = get_venv_executable(venv_root, "dg")
    assert dagster_components_path.exists()
    result = subprocess.run(
        [str(dagster_components_path), "list", "components", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def _get_component_types_in_python_environment(venv_root: Path) -> Sequence[str]:
    result = _get_component_print_script_result(venv_root)

    component_type_list = json.loads(result.stdout)
    return [component_type["key"] for component_type in component_type_list]


def _find_repo_root():
    current = Path(__file__).parent
    while not (current / ".git").exists():
        if current == Path("/"):
            raise Exception("Could not find the repository root.")
        current = current.parent
    return current


def _generate_test_component_source(number: int) -> str:
    return textwrap.dedent(f"""
    from dagster import Component

    class TestComponent{number}(Component):
        def build_defs(self, context):
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


@pytest.mark.skipif(
    seven.IS_PYTHON_3_14, reason="uses dagster_dbt, but dbt-core doesn't support 3.14"
)
def test_components_from_dagster():
    common_deps: list[str] = []
    for pkg_name in [
        "dagster-shared",
        "dagster-cloud-cli",
        "dagster-dg-core",
        "dagster-pipes",
        "dagster",
        "dagster-dg-cli",
    ]:
        common_deps.extend(["-e", _get_editable_package_root(pkg_name)])

    dbt_root = _get_editable_package_root("dagster-dbt")
    sling_root = _get_editable_package_root("dagster-sling")

    # No extras
    with _temp_venv([*common_deps]) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster_dbt.DbtProjectComponent" not in component_types
        assert "dagster_sling.SlingReplicationCollectionComponent" not in component_types
        for t in ["FunctionComponent", "PythonScriptComponent", "UvRunComponent"]:
            assert f"dagster.{t}" in component_types

    with _temp_venv([*common_deps, "-e", dbt_root]) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster_dbt.DbtProjectComponent" in component_types
        assert "dagster_sling.SlingReplicationCollectionComponent" not in component_types

    with _temp_venv([*common_deps, "-e", sling_root]) as python_executable:
        python = get_venv_executable(python_executable, "python")
        # Sling prints when it downloads its executable - this ensures we don't get that
        # stdout when listing the component types subsequently.
        subprocess.check_call([str(python), "-c", "import dagster_sling"])
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster_dbt.DbtProjectComponent" not in component_types
        assert "dagster_sling.SlingReplicationCollectionComponent" in component_types


def test_all_components_have_defined_summary():
    registry = discover_entry_point_package_objects()
    for component_name, component_type in registry.items():
        if isinstance(component_type, type) and issubclass(component_type, dg.Component):
            assert get_package_entry_snap(EnvRegistryKey("a", "a"), component_type).summary, (
                f"Component {component_name} has no summary defined"
            )


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
    "dagster",
]

[project.entry-points]
"<ENTRY_POINT_GROUP>" = { dagster_foo = "dagster_foo.lib"}
"""

DAGSTER_FOO_LIB_ROOT = f"""
{_generate_test_component_source(1)}

from dagster_foo.lib.sub import TestComponent2
"""


@contextmanager
def isolated_venv_with_component_lib_dagster_foo(
    entry_point_group: str,
    pre_install_hook: Optional[Callable[[], None]] = None,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        with pushd(tmpdir):
            # Create test package that defines some components
            os.makedirs("dagster-foo")

            pyproject_toml_content = re.sub(
                r"<ENTRY_POINT_GROUP>", entry_point_group, DAGSTER_FOO_PYPROJECT_TOML
            )

            with open("dagster-foo/pyproject.toml", "w") as f:
                f.write(pyproject_toml_content)

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
                _get_editable_package_root("dagster-pipes"),
                "-e",
                _get_editable_package_root("dagster-shared"),
                "-e",
                _get_editable_package_root("dagster-cloud-cli"),
                "-e",
                _get_editable_package_root("dagster-dg-core"),
                "-e",
                _get_editable_package_root("dagster-dg-cli"),
                "-e",
                "dagster-foo",
            ]

            with _temp_venv(deps) as venv_root:
                yield venv_root


@pytest.mark.parametrize(
    "entry_point_group", [DG_PLUGIN_ENTRY_POINT_GROUP, *OLD_DG_PLUGIN_ENTRY_POINT_GROUPS]
)
def test_components_from_third_party_lib(entry_point_group: str):
    with isolated_venv_with_component_lib_dagster_foo(entry_point_group) as venv_root:
        component_types = _get_component_types_in_python_environment(venv_root)
        assert "dagster_foo.lib.TestComponent1" in component_types
        assert "dagster_foo.lib.TestComponent2" in component_types


@pytest.mark.parametrize(
    "entry_point_group", [DG_PLUGIN_ENTRY_POINT_GROUP, *OLD_DG_PLUGIN_ENTRY_POINT_GROUPS]
)
def test_bad_entry_point_error_message(entry_point_group: str):
    # Modify the entry point to point to a non-existent module. This has to be done before the
    # package is installed, which is why we use a pre-install hook.
    def pre_install_hook():
        with modify_toml(Path("dagster-foo/pyproject.toml")) as toml:
            set_toml_value(
                toml,
                ("project", "entry-points", entry_point_group, "dagster_foo"),
                "fake.module",
            )

    with isolated_venv_with_component_lib_dagster_foo(
        entry_point_group, pre_install_hook=pre_install_hook
    ) as venv_root:
        result = _get_component_print_script_result(venv_root)
        assert "Error loading entry point `fake.module`" in result.stdout
        assert entry_point_group in result.stdout
        assert result.returncode == 1
