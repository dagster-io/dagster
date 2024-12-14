import inspect
import json
import os
import subprocess
import sys
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest
import tomli
from click.testing import CliRunner
from dagster_dg.cli.generate import (
    generate_code_location_command,
    generate_component_command,
    generate_component_type_command,
    generate_deployment_command,
)
from dagster_dg.context import CodeLocationDirectoryContext
from dagster_dg.utils import discover_git_root, pushd


# This is a holder for code that is intended to be written to a file
def _example_component_type_baz():
    import click
    from dagster import AssetExecutionContext, Definitions, PipesSubprocessClient, asset
    from dagster_components import (
        Component,
        ComponentGenerateRequest,
        ComponentLoadContext,
        component,
    )
    from dagster_components.generate import generate_component_yaml
    from pydantic import BaseModel

    _SAMPLE_PIPES_SCRIPT = """
    from dagster_pipes import open_dagster_pipes

    context = open_dagster_pipes()
    context.report_asset_materialization({"alpha": "beta"})
    """

    class BazGenerateParams(BaseModel):
        filename: str = "sample.py"

        @staticmethod
        @click.command
        @click.option("--filename", type=str, default="sample.py")
        def cli(filename: str) -> "BazGenerateParams":
            return BazGenerateParams(filename=filename)

    @component(name="baz")
    class Baz(Component):
        generate_params_schema = BazGenerateParams

        @classmethod
        def generate_files(cls, request: ComponentGenerateRequest, params: BazGenerateParams):
            generate_component_yaml(request, {})
            with open(params.filename, "w") as f:
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
def isolated_example_code_location_bar(
    runner: CliRunner, in_deployment: bool = True
) -> Iterator[None]:
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    if in_deployment:
        with isolated_example_deployment_foo(runner), clean_module_cache("bar"):
            runner.invoke(
                generate_code_location_command,
                ["--use-editable-dagster", dagster_git_repo_dir, "bar"],
            )
            with pushd("code_locations/bar"):
                yield
    else:
        with runner.isolated_filesystem(), clean_module_cache("bar"):
            runner.invoke(
                generate_code_location_command,
                ["--use-editable-dagster", dagster_git_repo_dir, "bar"],
            )
            with pushd("bar"):
                yield


@contextmanager
def isolated_example_code_location_bar_with_component_type_baz(
    runner: CliRunner, in_deployment: bool = True
) -> Iterator[None]:
    with isolated_example_code_location_bar(runner, in_deployment):
        with open("bar/lib/__init__.py", "a") as f:
            f.write("from bar.lib.baz import Baz\n")
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


def test_generate_code_location_inside_deployment_success() -> None:
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

        # Check venv created
        assert Path("code_locations/bar/.venv").exists()
        assert Path("code_locations/bar/uv.lock").exists()

        with open("code_locations/bar/pyproject.toml") as f:
            toml = tomli.loads(f.read())

            # No tool.uv.sources added without --use-editable-dagster
            assert "uv" not in toml["tool"]


def test_generate_code_location_outside_deployment_success() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        assert Path("bar").exists()
        assert Path("bar/bar").exists()
        assert Path("bar/bar/lib").exists()
        assert Path("bar/bar/components").exists()
        assert Path("bar/bar_tests").exists()
        assert Path("bar/pyproject.toml").exists()

        # Check venv created
        assert Path("bar/.venv").exists()
        assert Path("bar/uv.lock").exists()


@pytest.mark.parametrize("mode", ["env_var", "arg"])
def test_generate_code_location_editable_dagster_success(mode: str, monkeypatch) -> None:
    runner = CliRunner()
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if mode == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = ["--use-editable-dagster", "--"]
    else:
        editable_args = ["--use-editable-dagster", str(dagster_git_repo_dir)]
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_code_location_command, [*editable_args, "bar"])
        assert result.exit_code == 0
        assert Path("code_locations/bar").exists()
        assert Path("code_locations/bar/pyproject.toml").exists()
        with open("code_locations/bar/pyproject.toml") as f:
            toml = tomli.loads(f.read())
            assert toml["tool"]["uv"]["sources"]["dagster"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/dagster",
                "editable": True,
            }
            assert toml["tool"]["uv"]["sources"]["dagster-pipes"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/dagster-pipes",
                "editable": True,
            }
            assert toml["tool"]["uv"]["sources"]["dagster-webserver"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/dagster-webserver",
                "editable": True,
            }
            assert toml["tool"]["uv"]["sources"]["dagster-components"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/libraries/dagster-components",
                "editable": True,
            }


def test_generate_code_location_editable_dagster_no_env_var_no_value_fails(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(
            generate_code_location_command, ["--use-editable-dagster", "--", "bar"]
        )
        assert result.exit_code != 0
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_generate_code_location_already_exists_fails() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "already exists" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_type_success(in_deployment: bool) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        assert Path("bar/lib/baz.py").exists()
        context = CodeLocationDirectoryContext.from_path(Path.cwd())
        assert context.has_component_type("bar.baz")


def test_generate_component_type_outside_code_location_fails() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_type_already_exists_fails(in_deployment: bool) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code != 0
        assert "already exists" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_no_params_success(in_deployment: bool) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar_with_component_type_baz(runner, in_deployment):
        result = runner.invoke(generate_component_command, ["bar.baz", "qux"])
        assert result.exit_code == 0
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/sample.py").exists()  # default filename
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: bar.baz" in component_yaml_path.read_text()


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_json_params_success(in_deployment: bool) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar_with_component_type_baz(runner, in_deployment):
        result = runner.invoke(
            generate_component_command,
            ["bar.baz", "qux", "--json-params", '{"filename": "hello.py"}'],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/hello.py").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: bar.baz" in component_yaml_path.read_text()


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_extra_args_success(in_deployment: bool) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar_with_component_type_baz(runner, in_deployment):
        result = runner.invoke(
            generate_component_command, ["bar.baz", "qux", "--", "--filename=hello.py"]
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/hello.py").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert "type: bar.baz" in component_yaml_path.read_text()


def test_generate_component_json_params_and_extra_args_fails() -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar_with_component_type_baz(runner):
        result = runner.invoke(
            generate_component_command,
            [
                "bar.baz",
                "qux",
                "--json-params",
                '{"filename": "hello.py"}',
                "--",
                "--filename=hello.py",
            ],
        )
        assert result.exit_code != 0
        assert "Detected both --json-params and EXTRA_ARGS" in result.output


def test_generate_component_outside_code_location_fails() -> None:
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_component_command, ["bar.baz", "qux"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_already_exists_fails(in_deployment: bool) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar_with_component_type_baz(runner, in_deployment):
        result = runner.invoke(generate_component_command, ["bar.baz", "qux"])
        assert result.exit_code == 0
        result = runner.invoke(generate_component_command, ["bar.baz", "qux"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_sling_replication_instance() -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        # We need to add dagster-embedded-elt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(
            ["uv", "add", "dagster-components[sling]", "dagster-embedded-elt"], check=True
        )
        result = runner.invoke(
            generate_component_command, ["dagster_components.sling_replication", "file_ingest"]
        )
        assert result.exit_code == 0
        assert Path("bar/components/file_ingest").exists()

        component_yaml_path = Path("bar/components/file_ingest/component.yaml")
        assert component_yaml_path.exists()
        assert "type: dagster_components.sling_replication" in component_yaml_path.read_text()

        replication_path = Path("bar/components/file_ingest/replication.yaml")
        assert replication_path.exists()
        assert "source: " in replication_path.read_text()


dbt_project_path = "../stub_code_locations/dbt_project_location/components/jaffle_shop"


@pytest.mark.parametrize(
    "params",
    [
        ["--json-params", json.dumps({"project_path": str(dbt_project_path)})],
        ["--", "--project-path", dbt_project_path],
    ],
)
def test_generate_dbt_project_instance(params) -> None:
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)
        result = runner.invoke(
            generate_component_command, ["dagster_components.dbt_project", "my_project", *params]
        )
        assert result.exit_code == 0
        assert Path("bar/components/my_project").exists()

        component_yaml_path = Path("bar/components/my_project/component.yaml")
        assert component_yaml_path.exists()
        assert "type: dagster_components.dbt_project" in component_yaml_path.read_text()
        assert (
            "stub_code_locations/dbt_project_location/components/jaffle_shop"
            in component_yaml_path.read_text()
        )
