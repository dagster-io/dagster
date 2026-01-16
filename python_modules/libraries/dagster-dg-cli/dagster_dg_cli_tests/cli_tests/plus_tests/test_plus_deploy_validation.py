"""Tests for validation in dg plus deploy commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar


@pytest.fixture
def logged_in_dg_cli_config(empty_dg_cli_config, monkeypatch):
    """Config with organization and token set."""
    config = DagsterPlusCliConfig(
        organization="hooli",
        user_token="fake-user-token",
        default_deployment="prod",
    )
    config.write()
    monkeypatch.setenv("DAGSTER_CLOUD_API_TOKEN", "fake-api-token")
    yield


@pytest.fixture
def empty_dg_cli_config(monkeypatch):
    """Empty config with no credentials."""
    with tempfile.TemporaryDirectory() as tmp_dg_dir:
        config_path = Path(tmp_dg_dir) / "dg.toml"
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        monkeypatch.delenv("DG_USE_EDITABLE_DAGSTER", raising=False)
        monkeypatch.delenv("DAGSTER_CLOUD_ORGANIZATION", raising=False)
        monkeypatch.delenv("DAGSTER_CLOUD_API_TOKEN", raising=False)
        monkeypatch.delenv("DAGSTER_CLOUD_DEPLOYMENT", raising=False)
        yield


@pytest.fixture(scope="module")
def runner():
    """CLI test runner."""
    with ProxyRunner.test(use_fixed_test_components=True) as the_runner:
        yield the_runner


@pytest.fixture
def project(runner):
    """Create an isolated test project."""
    with isolated_example_project_foo_bar(runner) as project_dir:
        yield project_dir


@responses.activate
def test_deploy_start_validates_yaml_schema(logged_in_dg_cli_config, project: Path, runner):
    """Test that valid configuration passes validation."""
    # Mock successful API connectivity check
    responses.add(
        responses.POST,
        "https://hooli.dagster.cloud/graphql",
        json={"data": {"organizationSettings": {"settings": "{}"}}},
    )

    # Mock init_impl to avoid actual deployment
    with patch("dagster_cloud_cli.commands.ci.init_impl"):
        result = runner.invoke("plus", "deploy", "start", "--yes")
        assert result.exit_code == 0, result.output
        assert "Configuration validated" in result.output


@responses.activate
def test_deploy_start_fails_on_invalid_yaml(logged_in_dg_cli_config, project: Path, runner):
    """Test that invalid YAML schema fails validation."""
    # Mock the temp YAML generation to create invalid YAML
    with patch(
        "dagster_dg_cli.cli.utils.create_temp_dagster_cloud_yaml_file",
        side_effect=lambda ctx, statedir: _create_invalid_yaml(statedir),
    ):
        result = runner.invoke("plus", "deploy", "start", "--yes")
        assert result.exit_code != 0
        assert "Configuration validation failed" in result.output


def test_deploy_start_fails_on_missing_api_token(empty_dg_cli_config, project: Path, runner):
    """Test that missing API token fails validation."""
    result = runner.invoke(
        "plus", "deploy", "start", "--organization=hooli", "--deployment=prod", "--yes"
    )
    assert result.exit_code != 0
    assert "Configuration validation failed" in result.output
    assert "DAGSTER_CLOUD_API_TOKEN" in result.output


@responses.activate
def test_deploy_start_fails_on_invalid_api_token(logged_in_dg_cli_config, project: Path, runner):
    """Test that invalid API token fails validation."""
    # Mock API returning authentication error
    responses.add(
        responses.POST,
        "https://hooli.dagster.cloud/graphql",
        json={"errors": [{"message": "Unauthorized"}]},
        status=401,
    )

    result = runner.invoke("plus", "deploy", "start", "--yes")
    assert result.exit_code != 0
    assert "Configuration validation failed" in result.output


@responses.activate
def test_deploy_start_succeeds_with_valid_config(logged_in_dg_cli_config, project: Path, runner):
    """Test that valid configuration passes all checks."""
    responses.add(
        responses.POST,
        "https://hooli.dagster.cloud/graphql",
        json={"data": {"organizationSettings": {"settings": "{}"}}},
    )

    with patch("dagster_cloud_cli.commands.ci.init_impl"):
        result = runner.invoke("plus", "deploy", "start", "--yes")
        assert result.exit_code == 0, result.output
        assert "Configuration validated" in result.output


@responses.activate
def test_deploy_start_eu_region_url(empty_dg_cli_config, project: Path, runner, monkeypatch):
    """Test that EU region uses correct URL format and passes dagster_env to init_impl."""
    config = DagsterPlusCliConfig(
        organization="hooli",
        user_token="fake-user-token",
        default_deployment="prod",
        url="https://eu.dagster.cloud",
    )
    config.write()
    monkeypatch.setenv("DAGSTER_CLOUD_API_TOKEN", "fake-api-token")

    responses.add(
        responses.POST,
        "https://hooli.eu.dagster.cloud/graphql",
        json={"data": {"organizationSettings": {"settings": "{}"}}},
    )

    with patch("dagster_cloud_cli.commands.ci.init_impl") as mock_init:
        result = runner.invoke("plus", "deploy", "start", "--yes")
        assert result.exit_code == 0, result.output
        assert "Configuration validated" in result.output

        # Verify that init_impl was called with dagster_env="eu"
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["dagster_env"] == "eu", (
            f"Expected dagster_env='eu', got {call_kwargs.get('dagster_env')}"
        )
        assert call_kwargs["organization"] == "hooli"


@responses.activate
def test_deploy_start_us_region_url(empty_dg_cli_config, project: Path, runner, monkeypatch):
    """Test that US region (default) passes dagster_env=None to init_impl."""
    config = DagsterPlusCliConfig(
        organization="hooli",
        user_token="fake-user-token",
        default_deployment="prod",
        url="https://dagster.cloud",  # US region URL
    )
    config.write()
    monkeypatch.setenv("DAGSTER_CLOUD_API_TOKEN", "fake-api-token")

    responses.add(
        responses.POST,
        "https://hooli.dagster.cloud/graphql",
        json={"data": {"organizationSettings": {"settings": "{}"}}},
    )

    with patch("dagster_cloud_cli.commands.ci.init_impl") as mock_init:
        result = runner.invoke("plus", "deploy", "start", "--yes")
        assert result.exit_code == 0, result.output
        assert "Configuration validated" in result.output

        # Verify that init_impl was called with dagster_env=None for US region
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["dagster_env"] is None, (
            f"Expected dagster_env=None, got {call_kwargs.get('dagster_env')}"
        )
        assert call_kwargs["organization"] == "hooli"


@responses.activate
def test_deploy_start_skip_validation_bypasses_checks(
    logged_in_dg_cli_config, project: Path, runner
):
    """Test that --skip-validation bypasses all validation checks."""
    with patch("dagster_cloud_cli.commands.ci.init_impl"):
        result = runner.invoke("plus", "deploy", "start", "--yes", "--skip-validation")
        assert result.exit_code == 0, result.output
        assert "Configuration validated" not in result.output


def test_deploy_start_skip_validation_with_missing_token(
    empty_dg_cli_config, project: Path, runner
):
    """Test that --skip-validation works even with missing API token."""
    with patch("dagster_cloud_cli.commands.ci.init_impl"):
        result = runner.invoke(
            "plus",
            "deploy",
            "start",
            "--organization=hooli",
            "--deployment=prod",
            "--yes",
            "--skip-validation",
        )
        assert result.exit_code == 0, result.output


def test_validation_errors_are_actionable(empty_dg_cli_config, project: Path, runner):
    """Test that error messages provide clear guidance."""
    result = runner.invoke(
        "plus", "deploy", "start", "--organization=hooli", "--deployment=prod", "--yes"
    )
    assert result.exit_code != 0
    assert "Configuration validation failed:" in result.output
    assert "DAGSTER_CLOUD_API_TOKEN" in result.output
    assert "--skip-validation" in result.output


def _create_invalid_yaml(statedir: str) -> str:
    """Create an invalid dagster_cloud.yaml file."""
    yaml_path = Path(statedir) / "dagster_cloud.yaml"
    # Write YAML with invalid structure (missing required 'locations' field)
    yaml_path.write_text("invalid: yaml\nstructure: true\n")
    return str(yaml_path)
