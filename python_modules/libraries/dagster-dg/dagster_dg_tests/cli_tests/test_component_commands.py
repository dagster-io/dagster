import json
import subprocess
import textwrap
from pathlib import Path

import pytest
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
    isolated_example_deployment_foo,
)

# ########################
# ##### GENERATE
# ########################


def test_component_generate_dynamic_subcommand_generation() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("component", "generate", "--help")
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
def test_component_generate_no_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "generate",
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
def test_component_generate_json_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "generate",
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
def test_component_generate_key_value_params_success(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "generate",
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


def test_component_generate_json_params_and_key_value_params_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "component",
            "generate",
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


def test_component_generate_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("component", "generate", "bar.baz", "qux")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


@pytest.mark.parametrize("in_deployment", [True, False])
def test_component_generate_already_exists_fails(in_deployment: bool) -> None:
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner, in_deployment):
        result = runner.invoke(
            "component",
            "generate",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "component",
            "generate",
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
            "component", "generate", "dagster_components.sling_replication", "file_ingest"
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
            "component",
            "generate",
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


# ########################
# ##### LIST
# ########################


def test_list_components_succeeds():
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "component",
            "generate",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke("component", "list")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            qux
        """).strip()
        )


def test_list_components_command_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("component", "list")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output
