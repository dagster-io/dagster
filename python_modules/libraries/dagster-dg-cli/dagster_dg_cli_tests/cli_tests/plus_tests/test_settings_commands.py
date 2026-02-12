"""Integration tests for settings commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from dagster_dg_cli.utils.plus import gql_mutations
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_dg_cli_tests.cli_tests.plus_tests.utils import mock_gql_response


@pytest.fixture
def settings_runner():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        yield runner


def _assert_override_config(
    runner,
    command_args: tuple[str, ...],
    command_patch_target: str,
    command_patch_return: object,
) -> None:
    with (
        patch(
            "dagster_dg_cli.cli.plus.settings.commands.DagsterPlusGraphQLClient.from_config"
        ) as mock_from_config,
        patch(command_patch_target) as mock_command_call,
    ):
        mock_from_config.return_value = object()
        mock_command_call.return_value = command_patch_return

        result = runner.invoke(
            "plus",
            "settings",
            *command_args,
            "--organization",
            "my-org",
            "--deployment",
            "staging",
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"
        called_config = mock_from_config.call_args.args[0]
        assert called_config.organization == "my-org"
        assert called_config.default_deployment == "staging"


@responses.activate
def test_get_settings_success(dg_plus_cli_config, settings_runner):
    mock_gql_response(
        query=gql_mutations.GET_DEPLOYMENT_SETTINGS_QUERY,
        json_data={
            "data": {
                "deploymentSettings": {
                    "settings": {
                        "auto_materialize": {"enabled": True, "minimum_interval_seconds": 30},
                        "telemetry": {"enabled": False},
                    }
                }
            }
        },
    )

    result = settings_runner.invoke("plus", "settings", "get")
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "auto_materialize" in result.output
    assert "telemetry" in result.output


def test_get_settings_no_auth(monkeypatch, settings_runner):
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        result = settings_runner.invoke("plus", "settings", "get")
        assert result.exit_code != 0
        assert "Organization not specified" in result.output or "dg plus login" in result.output


def test_get_settings_with_overrides_uses_override_config(dg_plus_cli_config, settings_runner):
    _assert_override_config(
        settings_runner,
        ("get",),
        "dagster_dg_cli.cli.plus.settings.commands.get_deployment_settings",
        {"telemetry": {"enabled": False}},
    )


@responses.activate
def test_get_settings_graphql_error(dg_plus_cli_config, settings_runner):
    mock_gql_response(
        query=gql_mutations.GET_DEPLOYMENT_SETTINGS_QUERY,
        json_data={"data": {"deploymentSettings": None}},
    )

    result = settings_runner.invoke("plus", "settings", "get")
    assert result.exit_code != 0
    assert "Unable to retrieve" in result.output


@responses.activate
def test_set_from_file_success(dg_plus_cli_config, tmp_path, settings_runner):
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text(
        """
auto_materialize:
  enabled: true
  minimum_interval_seconds: 60
telemetry:
  enabled: false
"""
    )

    mock_gql_response(
        query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
        json_data={
            "data": {
                "setDeploymentSettings": {
                    "__typename": "DeploymentSettings",
                    "settings": {
                        "auto_materialize": {"enabled": True, "minimum_interval_seconds": 60},
                        "telemetry": {"enabled": False},
                    },
                }
            }
        },
    )

    result = settings_runner.invoke("plus", "settings", "set-from-file", str(settings_file))
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "successfully" in result.output


def test_set_from_file_with_overrides_uses_override_config(
    dg_plus_cli_config, tmp_path, settings_runner
):
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text("telemetry:\n  enabled: false")

    _assert_override_config(
        settings_runner,
        ("set-from-file", str(settings_file)),
        "dagster_dg_cli.cli.plus.settings.commands.set_deployment_settings",
        {"telemetry": {"enabled": False}},
    )


@responses.activate
def test_set_from_file_empty_yaml(dg_plus_cli_config, tmp_path, settings_runner):
    settings_file = tmp_path / "empty_settings.yaml"
    settings_file.write_text("")

    mock_gql_response(
        query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
        json_data={
            "data": {"setDeploymentSettings": {"__typename": "DeploymentSettings", "settings": {}}}
        },
    )

    result = settings_runner.invoke("plus", "settings", "set-from-file", str(settings_file))
    assert result.exit_code == 0, f"Command failed: {result.output}"


def test_set_from_file_not_found(dg_plus_cli_config, settings_runner):
    result = settings_runner.invoke("plus", "settings", "set-from-file", "/nonexistent/file.yaml")
    assert result.exit_code != 0


@responses.activate
def test_set_from_file_graphql_error(dg_plus_cli_config, tmp_path, settings_runner):
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text("auto_materialize:\n  enabled: true")

    mock_gql_response(
        query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
        json_data={
            "data": {
                "setDeploymentSettings": {
                    "__typename": "PythonError",
                    "message": "Invalid settings configuration",
                }
            }
        },
    )

    result = settings_runner.invoke("plus", "settings", "set-from-file", str(settings_file))
    assert result.exit_code != 0
    assert "Invalid settings" in result.output


@responses.activate
def test_set_single_setting(dg_plus_cli_config, settings_runner):
    mock_gql_response(
        query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
        json_data={
            "data": {
                "setDeploymentSettings": {
                    "__typename": "DeploymentSettings",
                    "settings": {"auto_materialize": {"enabled": True}},
                }
            }
        },
    )

    result = settings_runner.invoke("plus", "settings", "set", "--auto-materialize-enabled", "true")
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "successfully" in result.output


@responses.activate
def test_set_multiple_settings(dg_plus_cli_config, settings_runner):
    mock_gql_response(
        query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
        json_data={
            "data": {
                "setDeploymentSettings": {
                    "__typename": "DeploymentSettings",
                    "settings": {
                        "auto_materialize": {"enabled": True, "minimum_interval_seconds": 60},
                        "telemetry": {"enabled": False},
                    },
                }
            }
        },
    )

    result = settings_runner.invoke(
        "plus",
        "settings",
        "set",
        "--auto-materialize-enabled",
        "true",
        "--auto-materialize-minimum-interval-seconds",
        "60",
        "--telemetry-enabled",
        "false",
    )
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "auto_materialize" in result.output
    assert "telemetry" in result.output


def test_set_no_settings_provided(dg_plus_cli_config, settings_runner):
    result = settings_runner.invoke("plus", "settings", "set")
    assert result.exit_code != 0
    assert "No settings provided" in result.output


@responses.activate
def test_set_with_deployment_override(dg_plus_cli_config, settings_runner):
    mock_gql_response(
        query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
        json_data={
            "data": {
                "setDeploymentSettings": {
                    "__typename": "DeploymentSettings",
                    "settings": {"telemetry": {"enabled": False}},
                }
            }
        },
    )

    result = settings_runner.invoke(
        "plus",
        "settings",
        "set",
        "--telemetry-enabled",
        "false",
        "--deployment",
        "staging",
    )
    assert result.exit_code == 0, f"Command failed: {result.output}"
