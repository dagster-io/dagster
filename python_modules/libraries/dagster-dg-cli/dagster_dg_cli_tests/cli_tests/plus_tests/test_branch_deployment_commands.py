"""Integration tests for branch deployment commands."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from dagster_dg_cli.utils.plus import gql_mutations
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_dg_cli_tests.cli_tests.plus_tests.utils import mock_gql_response


@pytest.fixture
def branch_deployment_runner():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        yield runner


@pytest.fixture
def git_repo_context(tmp_path):
    """Create a git repository context for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:test-org/test-repo.git"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    (repo_path / "test.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Test commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


@pytest.fixture
def branch_deployment_runner_in_git_repo(branch_deployment_runner, git_repo_context, monkeypatch):
    with monkeypatch.context() as m:
        m.chdir(git_repo_context)
        yield branch_deployment_runner


def test_create_or_update_no_auth(monkeypatch, branch_deployment_runner):
    """Test that create-or-update fails without authentication."""
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        with patch(
            "dagster_dg_cli.cli.plus.branch_deployment.commands.get_git_metadata_for_branch_deployment"
        ) as mock_git:
            mock_git.return_value = (
                Path.cwd(),
                "test-org/test-repo",
                "main",
                {
                    "commit_hash": "abc123",
                    "timestamp": 1234567890.0,
                    "author_name": "Test User",
                    "author_email": "test@example.com",
                    "commit_message": "Test commit",
                },
            )

            result = branch_deployment_runner.invoke(
                "plus", "branch-deployment", "create-or-update", "--read-git-state"
            )
            assert result.exit_code != 0
            error_output = f"{result.output}\n{result.exception or ''}"
            assert (
                "Unauthorized" in error_output
                or "401 Client Error" in error_output
                or "Organization not specified" in error_output
                or "dg plus login" in error_output
            )


@responses.activate
def test_create_or_update_with_read_git_state(
    dg_plus_cli_config, branch_deployment_runner_in_git_repo
):
    mock_gql_response(
        query=gql_mutations.CREATE_OR_UPDATE_BRANCH_DEPLOYMENT_MUTATION,
        json_data={
            "data": {
                "createOrUpdateBranchDeployment": {
                    "__typename": "DagsterCloudDeployment",
                    "deploymentId": 123,
                    "deploymentName": "test-org-test-repo-main",
                }
            }
        },
    )

    result = branch_deployment_runner_in_git_repo.invoke(
        "plus", "branch-deployment", "create-or-update", "--read-git-state"
    )
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "test-org-test-repo-main" in result.output
    assert "created/updated successfully" in result.output


@responses.activate
def test_create_or_update_with_manual_flags(
    dg_plus_cli_config, branch_deployment_runner_in_git_repo
):
    mock_gql_response(
        query=gql_mutations.CREATE_OR_UPDATE_BRANCH_DEPLOYMENT_MUTATION,
        json_data={
            "data": {
                "createOrUpdateBranchDeployment": {
                    "__typename": "DagsterCloudDeployment",
                    "deploymentId": 123,
                    "deploymentName": "test-org-test-repo-main",
                }
            }
        },
    )

    result = branch_deployment_runner_in_git_repo.invoke(
        "plus",
        "branch-deployment",
        "create-or-update",
        "--commit-hash",
        "abc123def456",
        "--timestamp",
        "1234567890",
    )
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "test-org-test-repo-main" in result.output


@responses.activate
def test_create_or_update_with_pr_metadata(
    dg_plus_cli_config, branch_deployment_runner_in_git_repo, git_repo_context
):
    mock_gql_response(
        query=gql_mutations.CREATE_OR_UPDATE_BRANCH_DEPLOYMENT_MUTATION,
        json_data={
            "data": {
                "createOrUpdateBranchDeployment": {
                    "__typename": "DagsterCloudDeployment",
                    "deploymentId": 123,
                    "deploymentName": "test-org-test-repo-feature",
                }
            }
        },
    )

    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=git_repo_context,
        check=True,
        capture_output=True,
    )

    result = branch_deployment_runner_in_git_repo.invoke(
        "plus",
        "branch-deployment",
        "create-or-update",
        "--read-git-state",
        "--pull-request-url",
        "https://github.com/test-org/test-repo/pull/123",
        "--pull-request-number",
        "123",
        "--pull-request-status",
        "open",
    )
    assert result.exit_code == 0, f"Command failed: {result.output}"


def test_create_or_update_missing_required_flags(
    dg_plus_cli_config, branch_deployment_runner_in_git_repo
):
    result = branch_deployment_runner_in_git_repo.invoke(
        "plus", "branch-deployment", "create-or-update"
    )
    assert result.exit_code != 0
    assert "--read-git-state" in result.output or "commit-hash" in result.output


def test_create_or_update_not_in_git_repo(dg_plus_cli_config, branch_deployment_runner):
    result = branch_deployment_runner.invoke(
        "plus",
        "branch-deployment",
        "create-or-update",
        "--commit-hash",
        "abc123",
        "--timestamp",
        "1234567890",
    )
    assert result.exit_code != 0
    assert "No git repository found" in result.output


@responses.activate
def test_create_or_update_graphql_error(dg_plus_cli_config, branch_deployment_runner_in_git_repo):
    mock_gql_response(
        query=gql_mutations.CREATE_OR_UPDATE_BRANCH_DEPLOYMENT_MUTATION,
        json_data={
            "data": {
                "createOrUpdateBranchDeployment": {
                    "__typename": "PythonError",
                    "message": "Something went wrong",
                }
            }
        },
    )

    result = branch_deployment_runner_in_git_repo.invoke(
        "plus", "branch-deployment", "create-or-update", "--read-git-state"
    )
    assert result.exit_code != 0
    assert "Something went wrong" in result.output


@responses.activate
def test_delete_success(dg_plus_cli_config, branch_deployment_runner):
    mock_gql_response(
        query=gql_mutations.GET_DEPLOYMENT_BY_NAME_QUERY,
        json_data={
            "data": {
                "deploymentByName": {
                    "__typename": "DagsterCloudDeployment",
                    "deploymentName": "test-branch",
                    "deploymentId": 456,
                    "deploymentType": "BRANCH",
                }
            }
        },
        expected_variables={"deploymentName": "test-branch"},
    )

    mock_gql_response(
        query=gql_mutations.DELETE_DEPLOYMENT_MUTATION,
        json_data={
            "data": {
                "deleteDeployment": {"__typename": "DagsterCloudDeployment", "deploymentId": 456}
            }
        },
        expected_variables={"deploymentId": 456},
    )

    result = branch_deployment_runner.invoke("plus", "branch-deployment", "delete", "test-branch")
    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert "deleted successfully" in result.output
    assert "test-branch" in result.output


@responses.activate
def test_delete_not_branch_deployment(dg_plus_cli_config, branch_deployment_runner):
    mock_gql_response(
        query=gql_mutations.GET_DEPLOYMENT_BY_NAME_QUERY,
        json_data={
            "data": {
                "deploymentByName": {
                    "__typename": "DagsterCloudDeployment",
                    "deploymentName": "prod",
                    "deploymentId": 789,
                    "deploymentType": "FULL",
                }
            }
        },
        expected_variables={"deploymentName": "prod"},
    )

    result = branch_deployment_runner.invoke("plus", "branch-deployment", "delete", "prod")
    assert result.exit_code != 0
    assert "not a branch deployment" in result.output


@responses.activate
def test_delete_deployment_not_found(dg_plus_cli_config, branch_deployment_runner):
    mock_gql_response(
        query=gql_mutations.GET_DEPLOYMENT_BY_NAME_QUERY,
        json_data={"data": {"deploymentByName": {"__typename": "NotFound"}}},
        expected_variables={"deploymentName": "nonexistent"},
    )

    result = branch_deployment_runner.invoke("plus", "branch-deployment", "delete", "nonexistent")
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "unable to find" in result.output.lower()


def test_delete_no_auth(monkeypatch, branch_deployment_runner):
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        result = branch_deployment_runner.invoke(
            "plus", "branch-deployment", "delete", "test-branch"
        )
        assert result.exit_code != 0
        error_output = f"{result.output}\n{result.exception or ''}"
        assert (
            "Unauthorized" in error_output
            or "401 Client Error" in error_output
            or "Organization not specified" in error_output
            or "dg plus login" in error_output
        )
