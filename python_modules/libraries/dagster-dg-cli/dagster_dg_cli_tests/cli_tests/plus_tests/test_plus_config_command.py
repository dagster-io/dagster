import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner
from dagster_dg_cli.cli.plus import plus_group
from dagster_shared.plus.config import DagsterPlusCliConfig


@pytest.fixture()
def setup_dg_cli_config(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_dg_dir,
        tempfile.TemporaryDirectory() as tmp_cloud_dir,
    ):
        config_path = Path(tmp_dg_dir) / "dg.toml"
        config_path.touch()
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(tmp_cloud_dir) / "config"))
        yield config_path


@pytest.fixture()
def setup_dg_cli_config_with_existing(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_dg_dir,
        tempfile.TemporaryDirectory() as tmp_cloud_dir,
    ):
        config_path = Path(tmp_dg_dir) / "dg.toml"
        config_path.write_text(
            '[cli.plus]\norganization = "existing-org"\nuser_token = "existing-token"\n'
        )
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(tmp_cloud_dir) / "config"))
        yield config_path


def test_config_set_all_fields(setup_dg_cli_config):
    """Token + org + deployment + region writes config correctly."""
    runner = CliRunner()
    result = runner.invoke(
        plus_group,
        [
            "config",
            "set",
            "--api-token",
            "my-token",
            "--organization",
            "hooli",
            "--deployment",
            "prod",
            "--region",
            "eu",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "organization: hooli" in result.output
    assert "deployment: prod" in result.output
    assert "url: https://eu.dagster.cloud" in result.output

    config = DagsterPlusCliConfig.get()
    assert config.organization == "hooli"
    assert config.user_token == "my-token"
    assert config.default_deployment == "prod"
    assert config.url == "https://eu.dagster.cloud"


def test_config_set_partial_update(setup_dg_cli_config_with_existing):
    """Setting only deployment on existing config preserves org/token."""
    runner = CliRunner()
    result = runner.invoke(
        plus_group,
        ["config", "set", "--deployment", "staging"],
    )
    assert result.exit_code == 0, result.output
    assert "deployment: staging" in result.output

    config = DagsterPlusCliConfig.get()
    assert config.organization == "existing-org"
    assert config.user_token == "existing-token"
    assert config.default_deployment == "staging"


def test_config_set_no_existing_config_missing_fields(setup_dg_cli_config):
    """No existing config and no org/token raises UsageError."""
    runner = CliRunner()
    result = runner.invoke(
        plus_group,
        ["config", "set", "--deployment", "prod"],
    )
    assert result.exit_code != 0
    assert "No existing configuration found" in result.output


def test_config_set_via_env_vars(setup_dg_cli_config, monkeypatch):
    """Env vars populate fields."""
    monkeypatch.setenv("DAGSTER_CLOUD_API_TOKEN", "env-token")
    monkeypatch.setenv("DAGSTER_CLOUD_ORGANIZATION", "env-org")
    runner = CliRunner()
    result = runner.invoke(plus_group, ["config", "set"])
    assert result.exit_code == 0, result.output
    assert "organization: env-org" in result.output

    config = DagsterPlusCliConfig.get()
    assert config.organization == "env-org"
    assert config.user_token == "env-token"


def test_config_set_eu_region(setup_dg_cli_config):
    """--region eu sets URL to EU endpoint."""
    runner = CliRunner()
    result = runner.invoke(
        plus_group,
        [
            "config",
            "set",
            "--api-token",
            "my-token",
            "--organization",
            "hooli",
            "--region",
            "eu",
        ],
    )
    assert result.exit_code == 0, result.output

    config = DagsterPlusCliConfig.get()
    assert config.url == "https://eu.dagster.cloud"


def test_config_set_url_override(setup_dg_cli_config):
    """--url directly sets url field."""
    runner = CliRunner()
    result = runner.invoke(
        plus_group,
        [
            "config",
            "set",
            "--api-token",
            "my-token",
            "--organization",
            "hooli",
            "--url",
            "https://custom.dagster.cloud",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "url: https://custom.dagster.cloud" in result.output

    config = DagsterPlusCliConfig.get()
    assert config.url == "https://custom.dagster.cloud"
