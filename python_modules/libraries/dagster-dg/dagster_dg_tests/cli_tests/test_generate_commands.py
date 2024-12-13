import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest
import tomli
from dagster_dg.context import CodeLocationDirectoryContext, DgContext
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
    isolated_example_deployment_foo,
)


def test_generate_deployment_command_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("generate", "deployment", "foo")
        assert_runner_result(result)
        assert Path("foo").exists()
        assert Path("foo/.github").exists()
        assert Path("foo/.github/workflows").exists()
        assert Path("foo/.github/workflows/dagster-cloud-deploy.yaml").exists()
        assert Path("foo/dagster_cloud.yaml").exists()
        assert Path("foo/code_locations").exists()


def test_generate_deployment_command_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke("generate", "deployment", "foo")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_generate_code_location_inside_deployment_success() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("generate", "code-location", "bar")
        assert_runner_result(result)
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
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("generate", "code-location", "bar")
        assert_runner_result(result)
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
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if mode == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = ["--use-editable-dagster", "--"]
    else:
        editable_args = ["--use-editable-dagster", str(dagster_git_repo_dir)]
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("generate", "code-location", *editable_args, "bar")
        assert_runner_result(result)
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
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("generate", "code-location", "--use-editable-dagster", "--", "bar")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_generate_code_location_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("generate", "code-location", "bar")
        assert_runner_result(result)
        result = runner.invoke("generate", "code-location", "bar")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_type_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke("generate", "component-type", "baz")
        assert_runner_result(result)
        assert Path("bar/lib/baz.py").exists()
        context = CodeLocationDirectoryContext.from_path(Path.cwd(), DgContext.default())
        assert context.has_component_type("bar.baz")


def test_generate_component_type_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("generate", "component-type", "baz")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_type_already_exists_fails(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke("generate", "component-type", "baz")
        assert_runner_result(result)
        result = runner.invoke("generate", "component-type", "baz")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


def test_generate_component_dynamic_subcommand_generation() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("generate", "component", "--help")
        assert_runner_result(result)
        assert (
            textwrap.dedent("""
            Commands:
              dagster_components.test.all_metadata_empty_asset
              dagster_components.test.simple_asset
              dagster_components.test.simple_pipes_script_asset
        """).strip()
            in result.output
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_no_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.all_metadata_empty_asset"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_json_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.simple_pipes_script_asset",
            "qux",
            "--json-params",
            '{"asset_key": "foo", "filename": "hello.py"}',
        )
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/hello.py").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.simple_pipes_script_asset"
            in component_yaml_path.read_text()
        )


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_key_value_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.simple_pipes_script_asset",
            "qux",
            "--asset-key=foo",
            "--filename=hello.py",
        )
        assert_runner_result(result)
        assert Path("bar/components/qux").exists()
        assert Path("bar/components/qux/hello.py").exists()
        component_yaml_path = Path("bar/components/qux/component.yaml")
        assert component_yaml_path.exists()
        assert (
            "type: dagster_components.test.simple_pipes_script_asset"
            in component_yaml_path.read_text()
        )


def test_generate_component_json_params_and_key_value_params_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.simple_pipes_script_asset",
            "qux",
            "--json-params",
            '{"filename": "hello.py"}',
            "--filename=hello.py",
        )
        assert_runner_result(result, exit_0=False)
        assert (
            "Detected params passed as both --json-params and individual options" in result.output
        )


def test_generate_component_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("generate", "component", "bar.baz", "qux")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_generate_component_already_exists_fails(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### REAL COMPONENTS
# ########################


def test_generate_sling_replication_instance() -> None:
    with (
        ProxyRunner.test(use_test_component_lib=False) as runner,
        isolated_example_code_location_bar(runner),
    ):
        # We need to add dagster-embedded-elt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(
            ["uv", "add", "dagster-components[sling]", "dagster-embedded-elt"], check=True
        )
        result = runner.invoke(
            "generate", "component", "dagster_components.sling_replication", "file_ingest"
        )
        assert_runner_result(result)
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
        ["--project-path", dbt_project_path],
    ],
)
def test_generate_dbt_project_instance(params) -> None:
    with (
        ProxyRunner.test(use_test_component_lib=False) as runner,
        isolated_example_code_location_bar(runner),
    ):
        # We need to add dagster-dbt also because we are using editable installs. Only
        # direct dependencies will be resolved by uv.tool.sources.
        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.dbt_project",
            "my_project",
            *params,
        )
        assert_runner_result(result)
        assert Path("bar/components/my_project").exists()

        component_yaml_path = Path("bar/components/my_project/component.yaml")
        assert component_yaml_path.exists()
        assert "type: dagster_components.dbt_project" in component_yaml_path.read_text()
        assert (
            "stub_code_locations/dbt_project_location/components/jaffle_shop"
            in component_yaml_path.read_text()
        )
