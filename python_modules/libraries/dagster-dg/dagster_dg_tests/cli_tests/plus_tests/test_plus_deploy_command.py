import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from dagster_dg.cli.plus import plus_group
from dagster_dg.cli.plus.deploy import DEFAULT_STATEDIR_PATH
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


@pytest.fixture
def build_yaml_file(project):
    build_yaml_path = "build.yaml"
    try:
        with open(build_yaml_path, "w") as f:
            f.write("registry: my-repo\ndirectory: .")
        yield build_yaml_path
    finally:
        Path(build_yaml_path).unlink()


@pytest.fixture(scope="module")
def runner():
    yield CliRunner()


@pytest.fixture(scope="module")
def project(runner):
    with isolated_example_project_foo_bar(
        runner, use_editable_dagster=False, in_workspace=False
    ) as project_path:
        yield project_path


def _assert_dagster_cloud_cli_called_with(
    mock_external_dagster_cloud_cli_command, expected_args_list
):
    assert len(mock_external_dagster_cloud_cli_command.call_args_list) == len(expected_args_list)

    for i in range(len(expected_args_list)):
        expected_args = expected_args_list[i]
        actual_args = mock_external_dagster_cloud_cli_command.call_args_list[i][0][0]

        assert len(expected_args) == len(actual_args)
        assert all(
            expected_args[i] in [actual_args[i], mock.ANY] for i in range(len(expected_args))
        )


def test_plus_deploy_command_serverless(logged_in_dg_cli_config, project, runner):
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ) as mock_external_dagster_cloud_cli_command:
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0, result.output + " : " + str(result.exception)
        assert "No Dockerfile found - scaffolding a default one" in result.output

        assert len(mock_external_dagster_cloud_cli_command.call_args_list) == 3

        _assert_dagster_cloud_cli_called_with(
            mock_external_dagster_cloud_cli_command,
            [
                [
                    "ci",
                    "init",
                    "--statedir",
                    DEFAULT_STATEDIR_PATH,
                    "--dagster-cloud-yaml-path",
                    mock.ANY,
                    "--project-dir",
                    str(project.resolve()),
                    "--deployment",
                    "prod",
                    "--organization",
                    "hooli",
                    "--clean-statedir",
                ],
                [
                    "ci",
                    "build-and-push",
                    "--statedir",
                    DEFAULT_STATEDIR_PATH,
                    "--dockerfile-path",
                    str(project / "Dockerfile"),
                ],
                ["ci", "deploy", "--statedir", DEFAULT_STATEDIR_PATH],
            ],
        )

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


def test_plus_deploy_on_branch(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="my-branch",
    )
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ):
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0
        assert (
            "Deploying to the branch deployment for my-branch, with prod as the base deployment"
            in result.output
        )


def test_plus_deploy_cant_determine_branch(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value=None,
    )
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ):
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0
        assert "Could not determine a git branch, so deploying to prod." in result.output


def test_plus_deploy_main_branch(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ):
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0
        assert "Current branch is main, so deploying to prod." in result.output


def test_plus_deploy_hybrid_no_build_yaml(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ):
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "hybrid", "--yes"])

        assert result.exit_code

        assert "No build config found. Please specify a registry" in result.output


def test_plus_deploy_hybrid_with_build_yaml(
    logged_in_dg_cli_config, project, runner, mocker, build_yaml_file
):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ) as mock_external_dagster_cloud_cli_command:
        with patch(
            "dagster_dg.cli.plus.deploy_session._build_hybrid_image",
        ):
            result = runner.invoke(plus_group, ["deploy", "--agent-type", "hybrid", "--yes"])
            assert not result.exit_code, result.output

            _assert_dagster_cloud_cli_called_with(
                mock_external_dagster_cloud_cli_command,
                [
                    [
                        "ci",
                        "init",
                        "--statedir",
                        DEFAULT_STATEDIR_PATH,
                        "--dagster-cloud-yaml-path",
                        mock.ANY,
                        "--project-dir",
                        str(project.resolve()),
                        "--deployment",
                        "prod",
                        "--organization",
                        "hooli",
                        "--clean-statedir",
                    ],
                    ["ci", "deploy", "--statedir", DEFAULT_STATEDIR_PATH],
                ],
            )


def test_plus_deploy_subcommands(logged_in_dg_cli_config, project, runner, mocker, build_yaml_file):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )

    with patch(
        "dagster_dg.context.DgContext.external_dagster_cloud_cli_command",
    ) as mock_external_dagster_cloud_cli_command:
        result = runner.invoke(plus_group, ["deploy", "start", "--yes"])
        assert not result.exit_code, result.output
        assert "Current branch is main, so deploying to prod." in result.output

        _assert_dagster_cloud_cli_called_with(
            mock_external_dagster_cloud_cli_command,
            [
                [
                    "ci",
                    "init",
                    "--statedir",
                    DEFAULT_STATEDIR_PATH,
                    "--dagster-cloud-yaml-path",
                    mock.ANY,
                    "--project-dir",
                    str(project.resolve()),
                    "--deployment",
                    "prod",
                    "--organization",
                    "hooli",
                    "--clean-statedir",
                ],
            ],
        )

        mock_external_dagster_cloud_cli_command.reset_mock()

        with patch(
            "dagster_dg.cli.plus.deploy_session._build_hybrid_image",
        ):
            result = runner.invoke(
                plus_group, ["deploy", "build-and-push", "--agent-type", "hybrid"]
            )
            assert not result.exit_code, result.output

        result = runner.invoke(
            plus_group, ["deploy", "build-and-push", "--agent-type", "serverless"]
        )
        assert not result.exit_code, result.output
        _assert_dagster_cloud_cli_called_with(
            mock_external_dagster_cloud_cli_command,
            [
                [
                    "ci",
                    "build-and-push",
                    "--statedir",
                    DEFAULT_STATEDIR_PATH,
                    "--dockerfile-path",
                    str(project / "Dockerfile"),
                ],
            ],
        )

        mock_external_dagster_cloud_cli_command.reset_mock()

        result = runner.invoke(plus_group, ["deploy", "set-build-output", "--image-tag", "foo"])
        assert not result.exit_code, result.output

        _assert_dagster_cloud_cli_called_with(
            mock_external_dagster_cloud_cli_command,
            [
                [
                    "ci",
                    "set-build-output",
                    "--statedir",
                    DEFAULT_STATEDIR_PATH,
                    "--location-name",
                    "foo-bar",
                    "--tag",
                    "foo",
                ],
            ],
        )

        mock_external_dagster_cloud_cli_command.reset_mock()

        result = runner.invoke(plus_group, ["deploy", "finish"])
        assert not result.exit_code, result.output

        _assert_dagster_cloud_cli_called_with(
            mock_external_dagster_cloud_cli_command,
            [
                [
                    "ci",
                    "deploy",
                    "--statedir",
                    DEFAULT_STATEDIR_PATH,
                ],
            ],
        )
