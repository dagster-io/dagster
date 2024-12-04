import importlib
import inspect
import os
import sys
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from click.testing import CliRunner
from dagster._utils import pushd
from dagster_components.cli.generate import (
    generate_code_location_command,
    generate_component_command,
    generate_component_type_command,
    generate_deployment_command,
)
from dagster_components.core.component import ComponentRegistry
from dagster_components.core.deployment import CodeLocationProjectContext


def _ensure_cwd_on_sys_path():
    if sys.path[0] != "":
        sys.path.insert(0, "")


def _assert_module_imports(module_name: str):
    _ensure_cwd_on_sys_path()
    assert importlib.import_module(module_name)


# This is a holder for code that is intended to be written to a file
def _example_component_type_baz():
    from dagster import AssetExecutionContext, Definitions, PipesSubprocessClient, asset
    from dagster_components import Component, ComponentLoadContext

    _SAMPLE_PIPES_SCRIPT = """
    from dagster_pipes import open_dagster_pipes

    context = open_dagster_pipes()
    context.report_asset_materialization({"alpha": "beta"})
    """

    class Baz(Component):
        @classmethod
        def generate_files(cls):
            with open("sample.py", "w") as f:
                f.write(_SAMPLE_PIPES_SCRIPT)

        def build_defs(self, context: ComponentLoadContext) -> Definitions:
            @asset
            def foo(context: AssetExecutionContext, client: PipesSubprocessClient):
                client.run(context=context, command=["python", "sample.py"])

            return Definitions(assets=[foo], resources={"client": PipesSubprocessClient()})


@contextmanager
def isolated_example_deployment_foo(runner: CliRunner) -> Iterator[None]:
    with runner.isolated_filesystem():
        runner.invoke(generate_deployment_command, ["foo"])
        with pushd("foo"):
            yield


@contextmanager
def isolated_example_code_location_bar(runner: CliRunner) -> Iterator[None]:
    with isolated_example_deployment_foo(runner), clean_module_cache("bar"):
        runner.invoke(generate_code_location_command, ["bar"])
        with pushd("code_locations/bar"):
            yield


@contextmanager
def isolated_example_code_location_bar_with_component_type_baz(runner: CliRunner) -> Iterator[None]:
    with isolated_example_code_location_bar(runner):
        with open("bar/lib/baz.py", "w") as f:
            component_type_source = textwrap.dedent(
                inspect.getsource(_example_component_type_baz).split("\n", 1)[1]
            )
            f.write(component_type_source)
        yield


@contextmanager
def clean_module_cache(module_name: str):
    prefix = f"{module_name}."
    keys_to_del = {
        key for key in sys.modules.keys() if key == module_name or key.startswith(prefix)
    }
    for key in keys_to_del:
        del sys.modules[key]
    yield


def test_generate_deployment_command_success() -> None:
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


def test_generate_deployment_command_already_exists_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke(generate_deployment_command, ["foo"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_code_location_success() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        assert Path("code_locations/bar").exists()
        assert Path("code_locations/bar/bar").exists()
        assert Path("code_locations/bar/bar/lib").exists()
        assert Path("code_locations/bar/bar/components").exists()
        assert Path("code_locations/bar/bar_tests").exists()
        assert Path("code_locations/bar/pyproject.toml").exists()


def test_generate_code_location_outside_deployment_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster deployment project" in result.output


def test_generate_code_location_already_exists_fails() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_component_type_success() -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        assert Path("bar/lib/baz.py").exists()
        _assert_module_imports("bar.lib.baz")
        context = CodeLocationProjectContext.from_path(Path.cwd(), ComponentRegistry.empty())
        assert context.has_component_type("baz")


def test_generate_component_type_outside_code_location_fails() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location project" in result.output


def test_generate_component_type_already_exists_fails() -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_component_success() -> None:
    runner = CliRunner()
    _ensure_cwd_on_sys_path()
    with isolated_example_code_location_bar_with_component_type_baz(runner):
        result = runner.invoke(generate_component_command, ["baz", "qux"])
        assert result.exit_code == 0
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/sample.py").exists()


def test_generate_component_outside_code_location_fails() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_component_command, ["baz", "qux"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location project" in result.output


def test_generate_component_already_exists_fails() -> None:
    runner = CliRunner()
    _ensure_cwd_on_sys_path()
    with isolated_example_code_location_bar_with_component_type_baz(runner):
        result = runner.invoke(generate_component_command, ["baz", "qux"])
        assert result.exit_code == 0
        result = runner.invoke(generate_component_command, ["baz", "qux"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_global_component_instance() -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(generate_component_command, ["sling_replication", "file_ingest"])
        assert result.exit_code == 0
        assert Path("bar/components/file_ingest").exists()

        defs_path = Path("bar/components/file_ingest/defs.yml")
        assert defs_path.exists()
        assert "component_type: sling_replication" in defs_path.read_text()

        replication_path = Path("bar/components/file_ingest/replication.yaml")
        assert replication_path.exists()
        assert "source: " in replication_path.read_text()
