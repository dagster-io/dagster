import contextlib
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import NamedTuple
from unittest import mock
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner
from dagster_dg.cli.plus import plus_group
from dagster_dg.cli.plus.deploy import DEFAULT_STATEDIR_PATH
from dagster_dg.utils import pushd
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


@pytest.fixture
def workspace_build_yaml_file(workspace):
    build_yaml_path = workspace / "build.yaml"
    try:
        with open(build_yaml_path, "w") as f:
            f.write("registry: my-workspace-repo\ndirectory: .")
        yield build_yaml_path
    finally:
        Path(build_yaml_path).unlink()


@pytest.fixture
def workspace_project_build_yaml_file(workspace):
    build_yaml_path = workspace / "foo-bar" / "build.yaml"
    try:
        with open(build_yaml_path, "w") as f:
            f.write("registry: my-project-repo\ndirectory: .")
        yield build_yaml_path
    finally:
        Path(build_yaml_path).unlink()


@pytest.fixture(scope="module")
def runner():
    yield CliRunner()


# make this a single project in a workspace and change the path instead


@pytest.fixture(scope="module")
def project_setup_path(runner):
    with isolated_example_project_foo_bar(
        runner, use_editable_dagster=False, in_workspace=True
    ) as project_path:
        yield project_path


@pytest.fixture
def workspace(project_setup_path):
    with pushd(project_setup_path.parent):
        try:
            yield project_setup_path.parent
        finally:
            if (project_setup_path / "Dockerfile").exists():
                (project_setup_path / "Dockerfile").unlink()


@pytest.fixture
def project(project_setup_path):
    with pushd(project_setup_path):
        try:
            yield project_setup_path
        finally:
            if (project_setup_path / "Dockerfile").exists():
                (project_setup_path / "Dockerfile").unlink()


class MockedCloudCliCommands(NamedTuple):
    init: mock.MagicMock
    build: mock.MagicMock
    deploy: mock.MagicMock
    set_build_output: mock.MagicMock

    def reset_mocks(self):
        self.init.reset_mock()
        self.build.reset_mock()
        self.deploy.reset_mock()
        self.set_build_output.reset_mock()


@contextlib.contextmanager
def mock_external_dagster_cloud_cli_command() -> Generator[MockedCloudCliCommands, None, None]:
    with (
        patch(
            "dagster_cloud_cli.commands.ci.init_impl",
        ) as mock_init_command,
        patch(
            "dagster_cloud_cli.commands.ci.build_impl",
        ) as mock_build_command,
        patch(
            "dagster_cloud_cli.commands.ci.deploy_impl",
        ) as mock_deploy_command,
        patch(
            "dagster_cloud_cli.commands.ci.set_build_output_impl",
        ) as mock_set_build_output_command,
    ):
        yield MockedCloudCliCommands(
            init=mock_init_command,
            build=mock_build_command,
            deploy=mock_deploy_command,
            set_build_output=mock_set_build_output_command,
        )


def test_plus_deploy_command_serverless(logged_in_dg_cli_config, project: Path, runner):
    with (
        mock_external_dagster_cloud_cli_command() as mocked_cloud_cli_commands,
    ):
        from dagster_cloud_cli.commands.ci import BuildStrategy
        from dagster_cloud_cli.core.pex_builder import deps

        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0, result.output + " : " + str(result.exception)
        assert "No Dockerfile found - scaffolding a default one" in result.output

        mocked_cloud_cli_commands.init.assert_called_with(
            statedir=DEFAULT_STATEDIR_PATH,
            project_dir=str(project.resolve()),
            deployment="prod",
            organization="hooli",
            clean_statedir=False,
            dagster_cloud_yaml_path=mock.ANY,
            commit_hash=None,
            require_branch_deployment=False,
            git_url=None,
            dagster_env=None,
            location_name=tuple(),
            snapshot_base_condition=None,
            status_url=None,
        )
        mocked_cloud_cli_commands.build.assert_called_once_with(
            statedir=DEFAULT_STATEDIR_PATH,
            build_directory=str(project.resolve()),
            dockerfile_path=str((project / "Dockerfile").absolute()),
            use_editable_dagster=False,
            build_strategy=BuildStrategy.docker,
            docker_image_tag=None,
            docker_base_image=None,
            docker_env=[],
            python_version="3.11",
            pex_build_method=deps.BuildMethod.LOCAL,
            pex_deps_cache_from=None,
            pex_deps_cache_to=None,
            pex_base_image_tag=None,
            location_name=["foo-bar"],
        )
        mocked_cloud_cli_commands.deploy.assert_called_once_with(
            statedir=DEFAULT_STATEDIR_PATH,
            agent_heartbeat_timeout=mock.ANY,
            location_load_timeout=mock.ANY,
            location_name=tuple(),
        )

        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert "Building using Dockerfile at" in result.output
        assert result.exit_code == 0, result.output + " : " + str(result.exception)


def test_plus_deploy_command_serverless_workspace(logged_in_dg_cli_config, workspace, runner):
    with (
        mock_external_dagster_cloud_cli_command() as mocked_cloud_cli_commands,
    ):
        from dagster_cloud_cli.commands.ci import BuildStrategy
        from dagster_cloud_cli.core.pex_builder import deps

        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0, result.output + " : " + str(result.exception)
        assert "No Dockerfile found - scaffolding a default one" in result.output

        workspace_project_path = workspace / "foo-bar"

        mocked_cloud_cli_commands.init.assert_called_with(
            statedir=DEFAULT_STATEDIR_PATH,
            project_dir=str(workspace.resolve()),
            deployment="prod",
            organization="hooli",
            clean_statedir=False,
            dagster_cloud_yaml_path=mock.ANY,
            commit_hash=None,
            require_branch_deployment=False,
            git_url=None,
            location_name=tuple(),
            dagster_env=None,
            snapshot_base_condition=None,
            status_url=None,
        )
        mocked_cloud_cli_commands.build.assert_called_once_with(
            statedir=DEFAULT_STATEDIR_PATH,
            build_directory=str(workspace_project_path.resolve()),
            dockerfile_path=str((workspace_project_path / "Dockerfile").resolve()),
            use_editable_dagster=False,
            build_strategy=BuildStrategy.docker,
            docker_image_tag=None,
            docker_base_image=None,
            docker_env=[],
            python_version="3.11",
            pex_build_method=deps.BuildMethod.LOCAL,
            pex_deps_cache_from=None,
            pex_deps_cache_to=None,
            pex_base_image_tag=None,
            location_name=["foo-bar"],
        )
        mocked_cloud_cli_commands.deploy.assert_called_once_with(
            statedir=DEFAULT_STATEDIR_PATH,
            agent_heartbeat_timeout=mock.ANY,
            location_load_timeout=mock.ANY,
            location_name=tuple(),
        )

        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert "Building using Dockerfile at" in result.output
        assert result.exit_code == 0, result.output + " : " + str(result.exception)


def test_plus_deploy_command_no_login(empty_dg_cli_config, runner, project):
    result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
    assert result.exit_code != 0
    assert "Organization not specified" in result.output


def test_plus_deploy_on_branch(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="my-branch",
    )
    with mock_external_dagster_cloud_cli_command():
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
    with mock_external_dagster_cloud_cli_command():
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0
        assert "Could not determine a git branch, so deploying to prod." in result.output


def test_plus_deploy_main_branch(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with mock_external_dagster_cloud_cli_command():
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "serverless", "--yes"])
        assert result.exit_code == 0
        assert "Current branch is main, so deploying to prod." in result.output


def test_plus_deploy_hybrid_no_build_yaml(logged_in_dg_cli_config, project, runner, mocker):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with mock_external_dagster_cloud_cli_command():
        result = runner.invoke(plus_group, ["deploy", "--agent-type", "hybrid", "--yes"])

        assert result.exit_code

        assert "No build registry found. Please specify a registry key" in result.output


def test_plus_deploy_hybrid_with_build_yaml(
    logged_in_dg_cli_config, project, runner, mocker, build_yaml_file
):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with mock_external_dagster_cloud_cli_command() as mocked_cloud_cli_commands:
        with patch(
            "dagster_dg.cli.plus.deploy_session._build_hybrid_image",
        ):
            result = runner.invoke(plus_group, ["deploy", "--agent-type", "hybrid", "--yes"])
            assert not result.exit_code, result.output

            mocked_cloud_cli_commands.init.assert_called_with(
                statedir=DEFAULT_STATEDIR_PATH,
                project_dir=str(project.resolve()),
                deployment="prod",
                organization="hooli",
                clean_statedir=False,
                commit_hash=None,
                dagster_cloud_yaml_path=mock.ANY,
                git_url=None,
                require_branch_deployment=False,
                dagster_env=None,
                location_name=tuple(),
                snapshot_base_condition=None,
                status_url=None,
            )
            mocked_cloud_cli_commands.deploy.assert_called_once_with(
                statedir=DEFAULT_STATEDIR_PATH,
                agent_heartbeat_timeout=mock.ANY,
                location_load_timeout=mock.ANY,
                location_name=tuple(),
            )


def test_plus_deploy_hybrid_with_workspace_build_yaml(
    logged_in_dg_cli_config, workspace, runner, mocker, workspace_build_yaml_file
):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )

    with (
        mock_external_dagster_cloud_cli_command() as mocked_cloud_cli_commands,
    ):
        with patch(
            "dagster_dg.cli.plus.deploy_session._build_hybrid_image",
        ):
            result = runner.invoke(plus_group, ["deploy", "--agent-type", "hybrid", "--yes"])
            assert not result.exit_code, result.output

            dagster_cloud_yaml_path = DEFAULT_STATEDIR_PATH / Path("dagster_cloud.yaml")

            mocked_cloud_cli_commands.init.assert_called_with(
                statedir=DEFAULT_STATEDIR_PATH,
                project_dir=str(workspace.resolve()),
                deployment="prod",
                organization="hooli",
                clean_statedir=False,
                commit_hash=None,
                dagster_cloud_yaml_path=mock.ANY,
                git_url=None,
                require_branch_deployment=False,
                dagster_env=None,
                location_name=tuple(),
                snapshot_base_condition=None,
                status_url=None,
            )

            mocked_cloud_cli_commands.deploy.assert_called_once_with(
                statedir=DEFAULT_STATEDIR_PATH,
                location_name=tuple(),
                agent_heartbeat_timeout=mock.ANY,
                location_load_timeout=mock.ANY,
            )

            with open(dagster_cloud_yaml_path) as f:
                assert yaml.safe_load(f)["locations"][0]["build"] == {
                    "directory": str(workspace.resolve()),  # from build.yaml
                    "registry": "my-workspace-repo",
                }


def test_plus_deploy_hybrid_with_merged_build_yaml(
    logged_in_dg_cli_config,
    workspace,
    runner,
    mocker,
    workspace_build_yaml_file,
    workspace_project_build_yaml_file,
):
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )
    with (
        mock_external_dagster_cloud_cli_command() as mocked_cloud_cli_commands,
    ):
        with patch(
            "dagster_dg.cli.plus.deploy_session._build_hybrid_image",
        ):
            result = runner.invoke(plus_group, ["deploy", "--agent-type", "hybrid", "--yes"])
            assert not result.exit_code, result.output

            dagster_cloud_yaml_path = DEFAULT_STATEDIR_PATH / Path("dagster_cloud.yaml")

            mocked_cloud_cli_commands.init.assert_called_with(
                statedir=DEFAULT_STATEDIR_PATH,
                project_dir=str(workspace.resolve()),
                deployment="prod",
                organization="hooli",
                clean_statedir=False,
                commit_hash=None,
                dagster_cloud_yaml_path=mock.ANY,
                git_url=None,
                require_branch_deployment=False,
                dagster_env=None,
                location_name=tuple(),
                snapshot_base_condition=None,
                status_url=None,
            )

            mocked_cloud_cli_commands.deploy.assert_called_once_with(
                statedir=DEFAULT_STATEDIR_PATH,
                location_name=tuple(),
                agent_heartbeat_timeout=mock.ANY,
                location_load_timeout=mock.ANY,
            )

            with open(dagster_cloud_yaml_path) as f:
                assert yaml.safe_load(f)["locations"][0]["build"] == {
                    "directory": str((workspace / "foo-bar").resolve()),  # from build.yaml
                    "registry": "my-project-repo",
                }


def test_plus_deploy_subcommands(
    logged_in_dg_cli_config, project, runner, mocker, build_yaml_file
) -> None:
    mocker.patch(
        "dagster_dg.cli.plus.deploy_session.get_local_branch_name",
        return_value="main",
    )

    with mock_external_dagster_cloud_cli_command() as mocked_cloud_cli_commands:
        from dagster_cloud_cli.commands.ci import BuildStrategy
        from dagster_cloud_cli.core.pex_builder import deps

        result = runner.invoke(plus_group, ["deploy", "start", "--yes"])
        assert not result.exit_code, result.output
        assert "Current branch is main, so deploying to prod." in result.output

        mocked_cloud_cli_commands.init.assert_called_with(
            statedir=DEFAULT_STATEDIR_PATH,
            project_dir=str(project.resolve()),
            deployment="prod",
            organization="hooli",
            clean_statedir=False,
            dagster_cloud_yaml_path=mock.ANY,
            commit_hash=None,
            git_url=None,
            require_branch_deployment=False,
            dagster_env=None,
            location_name=tuple(),
            snapshot_base_condition=None,
            status_url=None,
        )

        mocked_cloud_cli_commands.reset_mocks()

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
        mocked_cloud_cli_commands.build.assert_called_once_with(
            statedir=DEFAULT_STATEDIR_PATH,
            build_directory=str(project.resolve()),
            dockerfile_path=str((project / "Dockerfile").absolute()),
            use_editable_dagster=False,
            build_strategy=BuildStrategy.docker,
            docker_image_tag=None,
            docker_base_image=None,
            docker_env=[],
            python_version="3.11",
            pex_build_method=deps.BuildMethod.LOCAL,
            pex_deps_cache_from=None,
            pex_deps_cache_to=None,
            pex_base_image_tag=None,
            location_name=["foo-bar"],
        )

        mocked_cloud_cli_commands.reset_mocks()

        result = runner.invoke(plus_group, ["deploy", "set-build-output", "--image-tag", "foo"])
        assert not result.exit_code, result.output

        mocked_cloud_cli_commands.set_build_output.assert_called_once_with(
            DEFAULT_STATEDIR_PATH,
            tuple(),
            "foo",
        )

        mocked_cloud_cli_commands.reset_mocks()

        result = runner.invoke(plus_group, ["deploy", "finish"])
        assert not result.exit_code, result.output

        mocked_cloud_cli_commands.deploy.assert_called_once_with(
            statedir=DEFAULT_STATEDIR_PATH,
            agent_heartbeat_timeout=mock.ANY,
            location_load_timeout=mock.ANY,
            location_name=tuple(),
        )
