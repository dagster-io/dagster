import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

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
def mock_get_or_create_agent_token():
    with mock.patch(
        "dagster_dg.cli.scaffold._get_or_create_agent_token"
    ) as mock_get_or_create_agent_token:
        yield mock_get_or_create_agent_token


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


def test_scaffold_github_actions_command_success(
    dg_plus_cli_config,
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
    setup_populated_git_workspace,
):
    mock_has_github_cli.return_value = True
    mock_logged_in_to_github.return_value = True

    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "github-actions")
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
    assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    assert Path("dagster_cloud.yaml").exists()
    assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML


def test_scaffold_github_actions_command_success_project(
    dg_plus_cli_config,
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
):
    mock_has_github_cli.return_value = True
    mock_logged_in_to_github.return_value = True

    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        subprocess.run(["git", "init"], check=False)
        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

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


def test_scaffold_github_actions_command_no_plus_config(
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
    setup_populated_git_workspace,
    monkeypatch,
):
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))
        mock_has_github_cli.return_value = True
        mock_logged_in_to_github.return_value = True

        runner = setup_populated_git_workspace
        result = runner.invoke("scaffold", "github-actions", input="my-org\n")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert "Dagster Plus organization name: " in result.output
        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "my-org" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML


def test_scaffold_github_actions_command_no_git_root(
    dg_plus_cli_config,
    mock_has_github_cli: mock.Mock,
    mock_logged_in_to_github: mock.Mock,
):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        runner.invoke("scaffold", "project", "foo")
        runner.invoke("scaffold", "project", "bar")
        runner.invoke("scaffold", "project", "baz")
        yield runner

        mock_has_github_cli.return_value = True
        mock_logged_in_to_github.return_value = True

        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 1, result.output + " " + str(result.exception)
        assert "No git repository found" in result.output

        result = runner.invoke("scaffold", "github-actions", "--git-root", str(Path.cwd()))
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML
