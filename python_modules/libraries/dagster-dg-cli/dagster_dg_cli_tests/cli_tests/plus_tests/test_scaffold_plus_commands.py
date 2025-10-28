# ruff: noqa: I001 - import order differs between CI and local due to package installation differences
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

import pytest
import responses
import yaml
from dagster_aws.ecs.container_context import EcsContainerContext
from dagster_dg_core.utils import pushd
from dagster_docker.container_context import DockerContainerContext
from dagster_k8s.container_context import K8sContainerContext
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)

from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform
from dagster_dg_cli.cli.scaffold.github_actions import REGISTRY_INFOS
from dagster_dg_cli.utils.plus import gql
from dagster_dg_cli_tests.cli_tests.plus_tests.utils import (
    PYTHON_VERSION,
    mock_gql_response,
    mock_hybrid_response,
)


def _get_error_message(file: Path, details: dict[str, Any]):
    position = details["location"]
    line = position["line"]
    column = position["column"]

    file_contents = file.read_text().splitlines()
    contents_snippet = (
        "\n".join(file_contents[max(0, line - 3) : line])
        + "\n"
        + " " * (column - 1)
        + "^"
        + "\n"
        + "\n".join(file_contents[line : line + 3])
    )
    return f"Action validator found errors in {file}:\n{contents_snippet}\n\n{details['detail']}"


def validate_github_actions_workflow(workflow_path: Path, *, expected_version: str = "main"):
    """Runs action-validator on the given file, and asserts that it returns a zero exit code.
    Prints a nicely formatted error message if it does not.
    """
    assert f"@{expected_version}" in workflow_path.read_text(), (
        f"TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION should be replaced with @{expected_version} in the workflow"
    )
    assert "TEMPLATE_" not in workflow_path.read_text(), (
        "TEMPLATE_ placeholders should be replaced in the workflow"
    )
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


@responses.activate
def test_scaffold_build_artifacts_container_context_no_running_agent(
    dg_plus_cli_config,
    setup_populated_git_workspace: ProxyRunner,
):
    mock_gql_response(
        query=gql.DEPLOYMENT_INFO_QUERY,
        json_data={
            "data": {
                "currentDeployment": {"agentType": "HYBRID"},
                "agents": [
                    {
                        "status": "NOT_RUNNING",
                        "metadata": [{"key": "type", "value": json.dumps("K8sUserCodeLauncher")}],
                    },
                ],
            }
        },
    )
    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "build-artifacts")
    assert result.exit_code == 0, result.output + " " + str(result.exception)
    assert result.exit_code == 0, result.output + " " + str(result.exception)
    assert not (Path.cwd() / "container_context.yaml").exists()
    return


@responses.activate
@pytest.mark.parametrize(
    "agent_class_name, agent_platform, container_context_class",
    [
        ("K8sUserCodeLauncher", DgPlusAgentPlatform.K8S, K8sContainerContext),
        ("EcsUserCodeLauncher", DgPlusAgentPlatform.ECS, EcsContainerContext),
        ("DockerUserCodeLauncher", DgPlusAgentPlatform.DOCKER, DockerContainerContext),
        ("ProcessUserCodeLauncher", DgPlusAgentPlatform.LOCAL, None),
        ("Unknown", DgPlusAgentPlatform.UNKNOWN, None),
    ],
)
def test_scaffold_build_artifacts_container_context_platforms(
    dg_plus_cli_config,
    setup_populated_git_workspace: ProxyRunner,
    agent_class_name: str,
    agent_platform: DgPlusAgentPlatform,
    container_context_class: Optional[Any],
):
    mock_hybrid_response(agent_class=agent_class_name)
    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "build-artifacts")
    assert result.exit_code == 0, result.output + " " + str(result.exception)
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    if agent_platform in {DgPlusAgentPlatform.LOCAL, DgPlusAgentPlatform.UNKNOWN}:
        assert not (Path.cwd() / "container_context.yaml").exists()
        return

    assert (Path.cwd() / "container_context.yaml").exists()

    container_context_contents = Path("container_context.yaml").read_text()

    # replace the '# ' at the start of each line with ' '
    container_context_contents = "\n".join(
        line[2:] for line in container_context_contents.splitlines()
    )

    assert container_context_class is not None
    # validate that the example config can be parsed as a valid container context dict
    assert container_context_class.create_from_config(yaml.safe_load(container_context_contents))


@responses.activate
def test_scaffold_build_artifacts_command_workspace(
    dg_plus_cli_config, setup_populated_git_workspace: ProxyRunner
):
    mock_hybrid_response()
    assert not (Path.cwd() / "build.yaml").exists()
    assert not (Path.cwd() / "container_context.yaml").exists()
    assert not (Path.cwd() / "foo" / "build.yaml").exists()
    assert not (Path.cwd() / "foo" / "container_context.yaml").exists()
    assert not (Path.cwd() / "foo" / "Dockerfile").exists()

    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "build-artifacts")
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    assert (Path.cwd() / "build.yaml").exists()
    assert (Path.cwd() / "container_context.yaml").exists()

    assert (Path.cwd() / "foo" / "build.yaml").exists()
    assert (Path.cwd() / "foo" / "container_context.yaml").exists()
    assert (Path.cwd() / "foo" / "Dockerfile").exists()

    modified_build_yaml = yaml.dump({"registry": "junk", "directory": "."}, sort_keys=True)

    (Path("foo") / "build.yaml").write_text(modified_build_yaml)

    modified_container_context_yaml = yaml.dump({"k8s": "junk"})
    (Path("foo") / "container_context.yaml").write_text(modified_container_context_yaml)
    (Path("foo") / "Dockerfile").write_text("junk")

    result = runner.invoke(
        "scaffold",
        "build-artifacts",
        input="N\nN\nN\nN\nN\nN\nN\nN\nN\nN\nN\n",
    )
    assert result.exit_code == 0, result.output + " " + str(result.exception)
    assert "Build config already exists" in result.output
    assert "Dockerfile already exists" in result.output
    assert "Container config already exists" in result.output
    assert (Path("foo") / "build.yaml").read_text() == modified_build_yaml
    assert (Path("foo") / "container_context.yaml").read_text() == modified_container_context_yaml
    assert (Path("foo") / "Dockerfile").read_text() == "junk"

    result = runner.invoke(
        "scaffold",
        "build-artifacts",
        input="Y\nY\nY\nY\nY\nY\nY\nY\nY\nY\nY\n",
    )
    assert result.exit_code == 0, result.output + " " + str(result.exception)

    assert "Build config already exists" in result.output
    assert "Dockerfile already exists" in result.output
    assert "Container config already exists" in result.output

    assert (Path("foo") / "build.yaml").read_text() != modified_build_yaml
    assert (Path("foo") / "Dockerfile").read_text() != "junk"
    assert (Path("foo") / "container_context.yaml").read_text() != modified_container_context_yaml
    # Test --yes flag skips confirmation prompts
    result = runner.invoke("scaffold", "build-artifacts", "--yes")
    assert result.exit_code == 0, result.output + " " + str(result.exception)


@responses.activate
def test_scaffold_build_artifacts_command_project(
    dg_plus_cli_config, setup_populated_git_workspace: ProxyRunner
):
    mock_hybrid_response()
    with pushd("foo"):
        assert not Path("build.yaml").exists()
        assert not Path("container_context.yaml").exists()
        assert not Path("Dockerfile").exists()

        runner = setup_populated_git_workspace
        result = runner.invoke("scaffold", "build-artifacts", "-y")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert Path("build.yaml").exists()
        assert Path("container_context.yaml").exists()
        assert Path("Dockerfile").exists()

        modified_build_yaml = yaml.dump({"registry": "junk", "directory": "."}, sort_keys=True)
        Path("build.yaml").write_text(modified_build_yaml)

        modified_container_context_yaml = yaml.dump({"k8s": "junk"})
        Path("container_context.yaml").write_text(modified_container_context_yaml)

        Path("Dockerfile").write_text("junk")

        result = runner.invoke(
            "scaffold",
            "build-artifacts",
            input="N\nN\nN\nN\nN\nN\nN\nN\nN\nN\nN\n",
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert "Build config already exists" in result.output
        assert "Dockerfile already exists" in result.output
        assert "Container config already exists" in result.output
        assert Path("build.yaml").read_text() == modified_build_yaml
        assert Path("container_context.yaml").read_text() == modified_container_context_yaml
        assert Path("Dockerfile").read_text() == "junk"

        result = runner.invoke(
            "scaffold",
            "build-artifacts",
            input="Y\nY\nY\nY\nY\nY\nY\nY\nY\nY\nY\n",
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert "Build config already exists" in result.output
        assert "Dockerfile already exists" in result.output
        assert "Container config already exists" in result.output

        assert Path("build.yaml").read_text() != modified_build_yaml, result.output
        assert Path("container_context.yaml").read_text() != modified_container_context_yaml, (
            result.output
        )
        assert Path("Dockerfile").read_text() != "junk", result.output


@pytest.fixture
def setup_populated_git_workspace():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        subprocess.run(["git", "init"], check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:hooli/example-repo.git"],
            check=True,
        )
        runner.invoke_create_dagster("project", "--no-uv-sync", "foo")
        runner.invoke_create_dagster("project", "--no-uv-sync", "bar")
        runner.invoke_create_dagster("project", "--no-uv-sync", "baz")
        yield runner


@responses.activate
@pytest.mark.parametrize(
    "version_override",
    [
        None,  # Use default version
        "1.11.0",  # Override version
    ],
)
def test_scaffold_github_actions_command_success_serverless(
    dg_plus_cli_config,
    setup_populated_git_workspace: ProxyRunner,
    version_override: Optional[str],
):
    from dagster_dg_cli import version

    current_version = version.__version__
    try:
        if version_override:
            version.__version__ = version_override

        mock_gql_response(
            query=gql.DEPLOYMENT_INFO_QUERY,
            json_data={"data": {"currentDeployment": {"agentType": "SERVERLESS"}}},
        )
        runner = setup_populated_git_workspace
        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert not Path("dagster_cloud.yaml").exists()
        assert "https://github.com/hooli/example-repo/settings/secrets/actions" in result.output

        expected_version = f"v{version_override}" if version_override else "main"
        validate_github_actions_workflow(
            Path(".github/workflows/dagster-plus-deploy.yml"),
            expected_version=expected_version,
        )
    finally:
        version.__version__ = current_version


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
        assert not Path("dagster_cloud.yaml").exists()

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
        assert not Path("dagster_cloud.yaml").exists()

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
        tempfile.TemporaryDirectory() as temp_dir,
        pushd(temp_dir),
    ):
        runner.invoke_create_dagster("workspace", "dagster-workspace")
        with pushd("dagster-workspace"):
            runner.invoke_create_dagster("project", "--uv-sync", "foo")
            runner.invoke_create_dagster("project", "--uv-sync", "bar")
            runner.invoke_create_dagster("project", "--uv-sync", "baz")

            result = runner.invoke("scaffold", "build-artifacts")
            assert result.exit_code == 0, result.output + " " + str(result.exception)

            result = runner.invoke("scaffold", "github-actions")
            assert result.exit_code == 1, result.output + " " + str(result.exception)
            assert "No git repository found" in result.output

            result = runner.invoke("scaffold", "github-actions", "--git-root", str(Path.cwd()))
            assert result.exit_code == 0, result.output + " " + str(result.exception)

            assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
            assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
            assert not Path("dagster_cloud.yaml").exists()

            validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


FAKE_ECR_URL = "10000.dkr.ecr.us-east-1.amazonaws.com"


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
    """Test that the command works with a top level workspace, with various Docker registry URLs."""
    mock_hybrid_response()

    runner = setup_populated_git_workspace
    result = runner.invoke("scaffold", "build-artifacts")
    assert result.exit_code == 0, result.output + " " + str(result.exception)
    Path("build.yaml").write_text(yaml.dump({"registry": registry_url}))

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
    assert not Path("dagster_cloud.yaml").exists()

    assert "https://github.com/hooli/example-repo/settings/secrets/actions" in result.output

    if registry_info.secrets_hints:
        for hint in registry_info.secrets_hints:
            assert hint in result.output

    validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_command_success_project_hybrid(
    dg_plus_cli_config,
):
    """Test that the command works with a top level project, no workspace."""
    mock_hybrid_response()
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        subprocess.run(["git", "init"], check=False)

        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 1, result.output + " " + str(result.exception)
        assert "No registry URL found" in result.output
        Path("build.yaml").write_text(yaml.dump({"registry": FAKE_ECR_URL, "build": "."}))

        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 1, result.output + " " + str(result.exception)
        assert "Dockerfile not found" in result.output

        result = runner.invoke(
            "scaffold", "build-artifacts", "--python-version", PYTHON_VERSION, input="\n"
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        result = runner.invoke("scaffold", "github-actions")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "hooli" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert not Path("dagster_cloud.yaml").exists()

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))
        assert f"python:{PYTHON_VERSION}-slim-bookworm" in Path("Dockerfile").read_text()


@responses.activate
def test_scaffold_github_actions_command_no_plus_config_hybrid(
    setup_populated_git_workspace,
    monkeypatch,
):
    """Test that the command works without dg.toml config."""
    with tempfile.TemporaryDirectory() as cloud_config_dir:
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))

        runner = setup_populated_git_workspace

        result = runner.invoke("scaffold", "build-artifacts")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        Path("build.yaml").write_text(yaml.dump({"registry": FAKE_ECR_URL}))

        result = runner.invoke(
            "scaffold",
            "github-actions",
            input="my-org\nprod\nhybrid\n",
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert "Dagster Plus organization name: " in result.output
        assert Path(".github/workflows/dagster-plus-deploy.yml").exists()
        assert "my-org" in Path(".github/workflows/dagster-plus-deploy.yml").read_text()
        assert not Path("dagster_cloud.yaml").exists()

        validate_github_actions_workflow(Path(".github/workflows/dagster-plus-deploy.yml"))


@responses.activate
def test_scaffold_github_actions_git_root_above_workspace(
    dg_plus_cli_config,
):
    """Test that the command works when the workspace is nested in the git repo rather than being the top-level directory."""
    mock_hybrid_response()
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        runner.invoke_create_dagster("project", "--uv-sync", "foo")

        # Setup git workspace in parent directory
        subprocess.run(["git", "init"], check=True, cwd=Path.cwd().parent)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:hooli/example-repo.git"],
            check=False,
        )
        result = runner.invoke("scaffold", "build-artifacts")
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        Path("build.yaml").write_text(yaml.dump({"registry": FAKE_ECR_URL}))

        result = runner.invoke(
            "scaffold",
            "github-actions",
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert (Path.cwd().parent / ".github" / "workflows" / "dagster-plus-deploy.yml").exists()
        assert (
            "hooli"
            in (Path.cwd().parent / ".github" / "workflows" / "dagster-plus-deploy.yml").read_text()
        )
        assert not Path("dagster_cloud.yaml").exists()

        validate_github_actions_workflow(
            Path.cwd().parent / ".github" / "workflows" / "dagster-plus-deploy.yml"
        )


@responses.activate
def test_scaffold_github_actions_git_root_above_project(
    dg_plus_cli_config,
):
    """Test that the command works when the project is nested in the git repo rather than being the top-level directory."""
    mock_hybrid_response()
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        tempfile.TemporaryDirectory() as temp_dir,
        pushd(temp_dir),
    ):
        runner.invoke_create_dagster("project", "--uv-sync", "foo")
        with pushd("foo"):
            # Setup git workspace in parent directory
            subprocess.run(["git", "init"], check=True, cwd=Path.cwd().parent)
            subprocess.run(
                ["git", "remote", "add", "origin", "git@github.com:hooli/example-repo.git"],
                check=False,
            )
            result = runner.invoke("scaffold", "build-artifacts")
            assert result.exit_code == 0, result.output + " " + str(result.exception)

            Path("build.yaml").write_text(yaml.dump({"registry": FAKE_ECR_URL}))

            result = runner.invoke(
                "scaffold",
                "github-actions",
            )
            assert result.exit_code == 0, result.output + " " + str(result.exception)

            assert (
                Path.cwd().parent / ".github" / "workflows" / "dagster-plus-deploy.yml"
            ).exists()
            assert (
                "hooli"
                in (
                    Path.cwd().parent / ".github" / "workflows" / "dagster-plus-deploy.yml"
                ).read_text()
            )
            assert not Path("dagster_cloud.yaml").exists()

            validate_github_actions_workflow(
                Path.cwd().parent / ".github" / "workflows" / "dagster-plus-deploy.yml"
            )
