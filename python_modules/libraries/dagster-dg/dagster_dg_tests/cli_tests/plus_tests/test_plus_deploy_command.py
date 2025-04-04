import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from dagster_dg.cli.plus import plus_group
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_tests.utils import isolated_example_project_foo_bar


@pytest.fixture
def logged_in_dg_cli_config(empty_dg_cli_config):
    config = DagsterPlusCliConfig(
        organization="hooli",
        user_token="fake-user-token",
        default_deployment="prod",
    )
    config.write()
    yield


@pytest.fixture
def empty_dg_cli_config(monkeypatch):
    with (
        tempfile.TemporaryDirectory() as tmp_dg_dir,
    ):
        config_path = Path(tmp_dg_dir) / "dg.toml"
        monkeypatch.setenv("DG_CLI_CONFIG", config_path)
        config = DagsterPlusCliConfig(
            organization="",
            user_token="",
            default_deployment="",
        )
        config.write()
        yield config_path


@pytest.fixture(scope="module")
def runner():
    yield CliRunner()


@pytest.fixture(scope="module")
def project(runner):
    with isolated_example_project_foo_bar(runner, use_editable_dagster=False, in_workspace=False):
        yield


def test_plus_deploy_command(logged_in_dg_cli_config, project, runner):
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ):
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0, result.output + " : " + str(result.exception)
        assert "No Dockerfile found - scaffolding a default one" in result.output

        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert "Building using Dockerfile at" in result.output
        assert result.exit_code == 0, result.output + " : " + str(result.exception)


def test_plus_deploy_command_no_login(empty_dg_cli_config, runner, project):
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ):
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code != 0
        assert "Organization not specified" in result.output
