"""Integration tests for settings commands."""

import tempfile
from pathlib import Path

import responses
from dagster_dg_cli.utils.plus import gql_mutations
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_dg_cli_tests.cli_tests.plus_tests.utils import mock_gql_response

########################################################
# GET COMMAND TESTS
########################################################


@responses.activate
def test_get_settings_success(dg_plus_cli_config):
    """Test successfully retrieving deployment settings."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
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

        result = runner.invoke("plus", "settings", "get")
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "auto_materialize" in result.output
        assert "telemetry" in result.output


def test_get_settings_no_auth(monkeypatch):
    """Test that get fails without authentication."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        tempfile.TemporaryDirectory() as cloud_config_dir,
    ):
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        result = runner.invoke("plus", "settings", "get")
        assert result.exit_code != 0
        assert "Organization not specified" in result.output or "dg plus login" in result.output


@responses.activate
def test_get_settings_graphql_error(dg_plus_cli_config):
    """Test handling of GraphQL errors."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql_mutations.GET_DEPLOYMENT_SETTINGS_QUERY,
            json_data={
                "data": {
                    "deploymentSettings": None  # Simulate error
                }
            },
        )

        result = runner.invoke("plus", "settings", "get")
        assert result.exit_code != 0
        assert "Unable to retrieve" in result.output or "settings" in result.output


########################################################
# SET-FROM-FILE COMMAND TESTS
########################################################


@responses.activate
def test_set_from_file_success(dg_plus_cli_config, tmp_path):
    """Test successfully setting settings from a YAML file."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        # Create a settings YAML file
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text("""
auto_materialize:
  enabled: true
  minimum_interval_seconds: 60
telemetry:
  enabled: false
""")

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

        result = runner.invoke("plus", "settings", "set-from-file", str(settings_file))
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "successfully" in result.output


@responses.activate
def test_set_from_file_empty_yaml(dg_plus_cli_config, tmp_path):
    """Test setting settings from an empty YAML file."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        # Create an empty settings file
        settings_file = tmp_path / "empty_settings.yaml"
        settings_file.write_text("")

        mock_gql_response(
            query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
            json_data={
                "data": {
                    "setDeploymentSettings": {
                        "__typename": "DeploymentSettings",
                        "settings": {},
                    }
                }
            },
        )

        result = runner.invoke("plus", "settings", "set-from-file", str(settings_file))
        assert result.exit_code == 0, f"Command failed: {result.output}"


def test_set_from_file_not_found(dg_plus_cli_config):
    """Test error when settings file doesn't exist."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("plus", "settings", "set-from-file", "/nonexistent/file.yaml")
        assert result.exit_code != 0


@responses.activate
def test_set_from_file_graphql_error(dg_plus_cli_config, tmp_path):
    """Test handling of GraphQL errors when setting from file."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
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

        result = runner.invoke("plus", "settings", "set-from-file", str(settings_file))
        assert result.exit_code != 0
        assert "Invalid settings" in result.output or "Failed" in result.output


########################################################
# SET COMMAND TESTS
########################################################


@responses.activate
def test_set_single_setting(dg_plus_cli_config):
    """Test setting a single setting via CLI flag."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
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

        result = runner.invoke("plus", "settings", "set", "--auto-materialize-enabled", "true")
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "successfully" in result.output


@responses.activate
def test_set_multiple_settings(dg_plus_cli_config):
    """Test setting multiple settings via CLI flags."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql_mutations.SET_DEPLOYMENT_SETTINGS_MUTATION,
            json_data={
                "data": {
                    "setDeploymentSettings": {
                        "__typename": "DeploymentSettings",
                        "settings": {
                            "auto_materialize": {"enabled": True, "minimum_interval": 60},
                            "telemetry": {"enabled": False},
                        },
                    }
                }
            },
        )

        result = runner.invoke(
            "plus",
            "settings",
            "set",
            "--auto-materialize-enabled",
            "true",
            "--auto-materialize-minimum-interval",
            "60",
            "--telemetry-enabled",
            "false",
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "auto_materialize" in result.output
        assert "telemetry" in result.output


def test_set_no_settings_provided(dg_plus_cli_config):
    """Test error when no settings flags are provided."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("plus", "settings", "set")
        assert result.exit_code != 0
        assert "No settings provided" in result.output


@responses.activate
def test_set_with_deployment_override(dg_plus_cli_config):
    """Test setting settings with --deployment flag override."""
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
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

        result = runner.invoke(
            "plus",
            "settings",
            "set",
            "--telemetry-enabled",
            "false",
            "--deployment",
            "staging",
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"
