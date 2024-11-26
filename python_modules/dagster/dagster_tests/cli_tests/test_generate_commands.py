import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path

from click.testing import CliRunner
from dagster._components import CodeLocationProjectContext
from dagster._components.cli.generate import (
    generate_code_location_command,
    generate_component_instance_command,
    generate_component_type_command,
    generate_deployment_command,
)


def _ensure_cwd_on_sys_path():
    if sys.path[0] != "":
        sys.path.insert(0, "")


def _assert_module_imports(module_name: str):
    _ensure_cwd_on_sys_path()
    assert importlib.import_module(module_name)


@contextmanager
def clean_module_cache(module_name: str):
    prefix = f"{module_name}."
    keys_to_del = {
        key for key in sys.modules.keys() if key == module_name or key.startswith(prefix)
    }
    for key in keys_to_del:
        del sys.modules[key]
    yield


def test_generate_deployment_command_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate_deployment_command, ["foo"])
        assert result.exit_code == 0
        assert Path("foo").exists()
        assert Path("foo/.github").exists()
        assert Path("foo/.github/workflows").exists()
        assert Path("foo/.github/workflows/dagster-cloud-deploy.yaml").exists()
        assert Path("foo/dagster_cloud.yaml").exists()
        assert Path("foo/code_locations").exists()


def test_generate_deployment_command_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke(generate_deployment_command, ["foo"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_code_location_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # set up deployment
        runner.invoke(generate_deployment_command, ["foo"])
        os.chdir("foo")

        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        assert Path("code_locations/bar").exists()
        assert Path("code_locations/bar/bar").exists()
        assert Path("code_locations/bar/bar/lib").exists()
        assert Path("code_locations/bar/bar/components").exists()
        assert Path("code_locations/bar/bar_tests").exists()
        assert Path("code_locations/bar/pyproject.toml").exists()


def test_generate_code_location_outside_deployment_fails():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster deployment project" in result.output


def test_generate_code_location_already_exists_fails():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # set up deployment
        runner.invoke(generate_deployment_command, ["foo"])
        os.chdir("foo")

        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_component_type_success():
    runner = CliRunner()
    with runner.isolated_filesystem(), clean_module_cache("bar"):
        # set up deployment
        runner.invoke(generate_deployment_command, ["foo"])
        os.chdir("foo")
        # set up code location
        runner.invoke(generate_code_location_command, ["bar"])
        os.chdir("code_locations/bar")

        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        assert Path("bar/lib/baz.py").exists()
        _assert_module_imports("bar.lib.baz")
        context = CodeLocationProjectContext.from_path(os.getcwd())
        assert context.has_component_type("bar.lib.baz[baz]")


_SAMPLE_COMPONENT_TYPE = """
from dagster import Component, Definitions, PipesSubprocessClient

_SAMPLE_PIPES_SCRIPT = \"""
from dagster_pipes import open_dagster_pipes

context = open_dagster_pipes()
context.report_asset_materialization({"alpha": "beta"})
\"""

class Baz(Component):

    @classmethod
    def generate_files(cls):
        with open("sample.py", "w") as f:
            f.write(_SAMPLE_PIPES_SCRIPT)

    def build_defs(self) -> Definitions:
        @asset
        def foo():
            PipesSubprocessClient("foo.py").run(context, command=["python", "sample.py"])

        return Definitions(
            assets=[foo]
        )

"""


def test_generate_component_instance_success():
    runner = CliRunner()
    _ensure_cwd_on_sys_path()
    with runner.isolated_filesystem(), clean_module_cache("bar"):
        # set up deployment
        runner.invoke(generate_deployment_command, ["foo"])
        os.chdir("foo")
        # set up code location
        runner.invoke(generate_code_location_command, ["bar"])
        os.chdir("code_locations/bar")
        # set up component type
        with open("bar/lib/baz.py", "w") as f:
            f.write(_SAMPLE_COMPONENT_TYPE)
        result = runner.invoke(generate_component_instance_command, ["bar.lib.baz[baz]", "qux"])
        assert result.exit_code == 0
        assert Path("bar/components/qux").exists()
