import subprocess
import tempfile
from pathlib import Path
from typing import Callable
from unittest import mock

import pytest
import responses
import yaml
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg.utils.plus import gql
from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response
from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


@pytest.fixture
def mock_has_github_cli():
    with mock.patch("dagster_dg.cli.scaffold._has_github_cli") as mock_has_github_cli:
        yield mock_has_github_cli


@pytest.fixture
def mock_logged_in_to_github():
    with mock.patch("dagster_dg.cli.scaffold._logged_in_to_github") as mock_logged_in_to_github:
        yield mock_logged_in_to_github


@pytest.fixture
def mock_add_github_secret():
    with mock.patch("dagster_dg.cli.scaffold._add_github_secret") as mock_add_github_secret:
        yield mock_add_github_secret


@pytest.fixture
def setup_populated_git_workspace():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        subprocess.run(["git", "init"], check=False)
        runner.invoke("scaffold", "project", "foo")
        runner.invoke("scaffold", "project", "bar")
        runner.invoke("scaffold", "project", "baz")
        yield runner


@pytest.fixture
def mock_token_gql_responses() -> Callable[[str], None]:
    def _mock(git_repo_name: str) -> None:
        mock_gql_response(
            query=gql.AGENT_TOKENS_QUERY,
            json_data={
                "data": {
                    "agentTokensOrError": {
                        "__typename": "AgentTokens",
                        "tokens": [],
                    }
                }
            },
        )

        mock_gql_response(
            query=gql.CREATE_AGENT_TOKEN_MUTATION,
            json_data={"data": {"createAgentToken": {"token": "abc123"}}},
            expected_variables={"description": f"Used in {git_repo_name} GitHub Actions"},
        )

    return _mock


EXPECTED_DAGSTER_CLOUD_YAML = {
    "locations": [
        {
            "build": {"directory": "foo"},
            "code_source": {"module_name": "foo.definitions"},
            "location_name": "foo",
        },
        {
            "build": {"directory": "bar"},
            "code_source": {"module_name": "bar.definitions"},
            "location_name": "bar",
        },
        {
            "build": {"directory": "baz"},
            "code_source": {"module_name": "baz.definitions"},
            "location_name": "baz",
        },
    ]
}


@responses.activate
def test_scaffold_github_actions_command_success(
    dg_plus_cli_config,
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
    mock_add_github_secret: mock.Mock,
    mock_token_gql_responses,
    setup_populated_git_workspace,
):
    mock_token_gql_responses("dagster-workspace")
    mock_has_github_cli.return_value = True
    mock_logged_in_to_github.return_value = "Logged in to GitHub"

    from dagster_dg.cli.scaffold import GITHUB_ACTIONS_WORKFLOW_URL

    responses.add_passthru(GITHUB_ACTIONS_WORKFLOW_URL)

    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "github-actions")
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    mock_add_github_secret.assert_called_once()

    assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
    assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    assert Path("dagster_cloud.yaml").exists()
    assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML


@responses.activate
def test_scaffold_github_actions_command_success_project(
    dg_plus_cli_config,
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
    mock_add_github_secret: mock.Mock,
    mock_token_gql_responses,
):
    mock_token_gql_responses("foo-bar")
    mock_has_github_cli.return_value = True
    mock_logged_in_to_github.return_value = "Logged in to GitHub"

    from dagster_dg.cli.scaffold import GITHUB_ACTIONS_WORKFLOW_URL

    responses.add_passthru(GITHUB_ACTIONS_WORKFLOW_URL)

    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        subprocess.run(["git", "init"], check=False)
        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        mock_add_github_secret.assert_called_once()

        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == {
            "locations": [
                {
                    "build": {"directory": "."},
                    "code_source": {"module_name": "foo_bar.definitions"},
                    "location_name": "foo-bar",
                }
            ]
        }


@pytest.mark.parametrize(
    "has_github_cli,is_logged_in",
    [
        (False, True),  # CLI not installed
        (True, False),  # CLI installed but not logged in
    ],
)
@responses.activate
def test_scaffold_github_actions_command_github_cli_issues(
    dg_plus_cli_config,
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
    mock_add_github_secret: mock.Mock,
    has_github_cli: bool,
    is_logged_in: bool,
    mock_token_gql_responses,
    setup_populated_git_workspace,
):
    mock_token_gql_responses("dagster-workspace")
    mock_has_github_cli.return_value = has_github_cli
    mock_logged_in_to_github.return_value = is_logged_in

    from dagster_dg.cli.scaffold import GITHUB_ACTIONS_WORKFLOW_URL

    responses.add_passthru(GITHUB_ACTIONS_WORKFLOW_URL)

    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "github-actions")
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    mock_add_github_secret.assert_not_called()
    assert (
        "Skipping GitHub secret creation because `gh` CLI is not installed or not logged in."
        in result.output
    )

    assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
    assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    assert Path("dagster_cloud.yaml").exists()
    assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML


@responses.activate
def test_scaffold_github_actions_command_no_plus_config(
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
    mock_add_github_secret: mock.Mock,
    mock_token_gql_responses,
    setup_populated_git_workspace,
    monkeypatch,
):
    mock_token_gql_responses("dagster-workspace")
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))
        mock_has_github_cli.return_value = True
        mock_logged_in_to_github.return_value = "Logged in to GitHub"

        from dagster_dg.cli.scaffold import GITHUB_ACTIONS_WORKFLOW_URL

        responses.add_passthru(GITHUB_ACTIONS_WORKFLOW_URL)

        runner = setup_populated_git_workspace
        result = runner.invoke("scaffold", "github-actions", input="my-org\n")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert not mock_add_github_secret.called

        assert "Dagster Plus organization name: " in result.output
        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "my-org" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML
