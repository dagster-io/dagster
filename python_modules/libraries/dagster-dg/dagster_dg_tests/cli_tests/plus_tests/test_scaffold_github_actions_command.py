import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest
import responses
import yaml
from dagster_dg.cli.scaffold import REGISTRY_INFOS
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dg.utils.plus import gql

ensure_dagster_dg_tests_import()


from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response
from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


def _get_error_message(file: Path, details: dict[str, Any]):
    position = details["location"]
    line = position["line"]
    column = position["column"]

    file_contents = file.read_text().splitlines()
    contents_snippet = (
        "\n".join(file_contents[line - 3 : line])
        + "\n"
        + " " * (column - 1)
        + "^"
        + "\n"
        + "\n".join(file_contents[line : line + 3])
    )
    return f"Action validator found errors in {file}:\n{contents_snippet}\n\n{details['detail']}"


def validate_github_actions_workflow(workflow_path: Path):
    """Runs action-validator on the given file, and asserts that it returns a zero exit code.
    Prints a nicely formatted error message if it does not.
    """
    result = subprocess.run(
        ["action-validator", str(workflow_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        details = json.loads(result.stderr)
        error_messages = "\n".join(
            [_get_error_message(workflow_path, error) for error in details["errors"]]
        )

        assert result.returncode == 0, (
            rf"Action validator found errors in {workflow_path}:\{error_messages}"
        )


@pytest.fixture
def setup_populated_git_workspace():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        subprocess.run(["git", "init"], check=False)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:hooli/example-repo.git"],
            check=False,
        )
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


@responses.activate
def test_scaffold_github_actions_command_success_serverless(
    dg_plus_cli_config,
    setup_populated_git_workspace: ProxyRunner,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "SERVERLESS"}}},
    )
    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "github-actions")
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
    assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    assert Path("dagster_cloud.yaml").exists()
    assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML
    assert "https://github.com/hooli/example-repo/settings/secrets/actions" in result.output

    validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_command_success_project_serverless(
    dg_plus_cli_config,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "SERVERLESS"}}},
    )
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

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_command_no_plus_config_serverless(
    setup_populated_git_workspace,
    monkeypatch,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "SERVERLESS"}}},
    )
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        runner = setup_populated_git_workspace
        result = runner.invoke("scaffold", "github-actions", input="my-org\nprod\nserverless\n")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert "Dagster Plus organization name: " in result.output
        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "my-org" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_command_no_git_root_serverless(
    dg_plus_cli_config,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "SERVERLESS"}}},
    )
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        runner.invoke("scaffold", "project", "foo")
        runner.invoke("scaffold", "project", "bar")
        runner.invoke("scaffold", "project", "baz")

        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 1, result.output + " " + str(result.exception)
        assert "No git repository found" in result.output

        result = runner.invoke("scaffold", "github-actions", "--git-root", str(Path.cwd()))
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == EXPECTED_DAGSTER_CLOUD_YAML

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


FAKE_ECR_URL = "10000.dkr.ecr.us-east-1.amazonaws.com"


def get_expected_dagster_cloud_yaml_hybrid(registry_url: str) -> dict:
    return {
        "locations": [
            {
                **location,
                "build": {**location["build"], "registry": registry_url},
            }
            for location in EXPECTED_DAGSTER_CLOUD_YAML["locations"]
        ]
    }


FAKE_REGISTRY_URLS = [
    "10000.dkr.ecr.us-east-1.amazonaws.com/hooli",
    "docker.io/hooli",
    "ghcr.io/hooli",
    "azurecr.io/hooli",
    "gcr.io/hooli",
]


@responses.activate
@pytest.mark.parametrize(
    "registry_url, registry_info",
    zip(FAKE_REGISTRY_URLS, REGISTRY_INFOS),
    ids=[info.name for info in REGISTRY_INFOS],
)
def test_scaffold_github_actions_command_success_hybrid(
    dg_plus_cli_config,
    setup_populated_git_workspace: ProxyRunner,
    registry_url,
    registry_info,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "HYBRID"}}},
    )

    Path("build.yaml").write_text(yaml.dump({"registry": registry_url}))

    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "github-actions")
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
    assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    assert (
        'Build and upload Docker image for "foo"'
        in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    )
    assert (
        'Build and upload Docker image for "bar"'
        in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    )
    assert (
        'Build and upload Docker image for "baz"'
        in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
    )
    assert Path("dagster_cloud.yaml").exists()
    assert yaml.safe_load(
        Path("dagster_cloud.yaml").read_text()
    ) == get_expected_dagster_cloud_yaml_hybrid(registry_url)
    assert "https://github.com/hooli/example-repo/settings/secrets/actions" in result.output

    if registry_info.secrets_hints:
        for hint in registry_info.secrets_hints:
            assert hint in result.output

    validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_command_success_project_hybrid(
    dg_plus_cli_config,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "HYBRID"}}},
    )
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        Path("build.yaml").write_text(yaml.dump({"registry": FAKE_ECR_URL}))

        subprocess.run(["git", "init"], check=False)
        result = runner.invoke(
            "scaffold",
            "github-actions",
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(Path("dagster_cloud.yaml").read_text()) == {
            "locations": [
                {
                    "build": {"directory": ".", "registry": FAKE_ECR_URL},
                    "code_source": {"module_name": "foo_bar.definitions"},
                    "location_name": "foo-bar",
                }
            ]
        }

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_command_no_plus_config_hybrid(
    setup_populated_git_workspace,
    monkeypatch,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={"data": {"currentDeployment": {"agentType": "HYBRID"}}},
    )
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        Path("build.yaml").write_text(yaml.dump({"registry": FAKE_ECR_URL}))

        runner = setup_populated_git_workspace
        result = runner.invoke(
            "scaffold",
            "github-actions",
            input="my-org\nprod\nhybrid\n",
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert "Dagster Plus organization name: " in result.output
        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "my-org" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert Path("dagster_cloud.yaml").exists()
        assert yaml.safe_load(
            Path("dagster_cloud.yaml").read_text()
        ) == get_expected_dagster_cloud_yaml_hybrid(FAKE_ECR_URL)

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))
