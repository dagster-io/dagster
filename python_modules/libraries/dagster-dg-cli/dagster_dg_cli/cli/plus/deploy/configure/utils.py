"""Shared utilities and constants for deployment configuration scaffolding."""

import subprocess
import textwrap
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import NamedTuple, Optional
from urllib.parse import urlparse

from dagster_dg_core.config import DgRawCliConfig
from dagster_dg_core.context import DgContext
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.record import record

from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform, DgPlusAgentType


class GitProvider(Enum):
    """Supported git providers for CI/CD scaffolding."""

    GITHUB = "github"
    GITLAB = "gitlab"


@record
class DgPlusDeployConfigureOptions:
    """Configuration options for Dagster Plus deployment configuration scaffolding."""

    dg_context: DgContext
    cli_config: DgRawCliConfig
    plus_config: Optional[DagsterPlusCliConfig]
    agent_type: DgPlusAgentType
    agent_platform: Optional[DgPlusAgentPlatform]
    organization_name: Optional[str]
    deployment_name: str
    git_root: Optional[Path]
    skip_confirmation_prompt: bool
    git_provider: Optional[GitProvider]
    use_editable_dagster: bool
    python_version: Optional[str]
    pex_deploy: Optional[bool] = None  # Only used for serverless
    registry_url: Optional[str] = None  # Only used for hybrid


def detect_agent_type_and_platform(
    plus_config: Optional[DagsterPlusCliConfig],
) -> tuple[Optional[DgPlusAgentType], Optional[DgPlusAgentPlatform]]:
    """Attempt to detect agent type and platform from Dagster Plus deployment.

    Returns:
        Tuple of (agent_type, platform). Both will be None if detection fails.
    """
    if not plus_config:
        return None, None

    try:
        from dagster_dg_cli.utils.plus.build import get_agent_type_and_platform_from_graphql
        from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

        gql_client = DagsterPlusGraphQLClient.from_config(plus_config)
        detected_type, detected_platform = get_agent_type_and_platform_from_graphql(gql_client)
        return detected_type, detected_platform
    except Exception:
        # If detection fails (no config, GraphQL error, etc.), return None
        return None, None


def get_cli_version_or_main() -> str:
    from dagster_dg_cli.version import __version__ as cli_version

    return "main" if cli_version.endswith("+dev") else f"v{cli_version}"


def search_for_git_root(path: Path) -> Optional[Path]:
    if path.joinpath(".git").exists():
        return path
    elif path.parent == path:
        return None
    else:
        return search_for_git_root(path.parent)


def get_project_contexts(dg_context: DgContext, cli_config: DgRawCliConfig) -> list[DgContext]:
    if dg_context.is_in_workspace:
        return [
            dg_context.for_project_environment(project.path, cli_config)
            for project in dg_context.project_specs
        ]
    else:
        return [dg_context]


def get_git_web_url(git_root: Path) -> Optional[str]:
    from dagster_cloud_cli.core.pex_builder.code_location import get_local_repo_name

    try:
        local_repo_name = get_local_repo_name(str(git_root))
        return f"https://github.com/{local_repo_name}"
    except subprocess.CalledProcessError:
        return None


def get_scaffolded_container_context_yaml(agent_platform: DgPlusAgentPlatform) -> Optional[str]:
    if agent_platform == DgPlusAgentPlatform.K8S:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for k8s resources.
            # k8s:
            #   server_k8s_config: # Raw kubernetes config for code servers launched by the agent
            #     pod_spec_config: # Config for the code server pod spec
            #       node_selector:
            #         disktype: standard
            #     pod_template_spec_metadata: # Metadata for the code server pod
            #       annotations:
            #         mykey: myvalue
            #     container_config: # Config for the main dagster container in the code server pod
            #       resources:
            #         limits:
            #           cpu: 100m
            #           memory: 128Mi
            #   run_k8s_config: # Raw kubernetes config for runs launched by the agent
            #     pod_spec_config: # Config for the run's PodSpec
            #       node_selector:
            #         disktype: ssd
            #     container_config: # Config for the main dagster container in the run pod
            #       resources:
            #         limits:
            #           cpu: 500m
            #           memory: 1024Mi
            #     pod_template_spec_metadata: # Metadata for the run pod
            #       annotations:
            #         mykey: myvalue
            #     job_spec_config: # Config for the Kubernetes job for the run
            #       ttl_seconds_after_finished: 7200
            """
        )
    elif agent_platform == DgPlusAgentPlatform.ECS:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for ECS resources.
            # ecs:
            #   env_vars:
            #     - DATABASE_NAME=staging
            #     - DATABASE_PASSWORD
            #   secrets:
            #     - name: 'MY_API_TOKEN'
            #       valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::'
            #     - name: 'MY_PASSWORD'
            #       valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:password::'
            #   server_resources: # Resources for code servers launched by the agent for this location
            #     cpu: "256"
            #     memory: "512"
            #   run_resources: # Resources for runs launched by the agent for this location
            #     cpu: "4096"
            #     memory: "16384"
            #   execution_role_arn: arn:aws:iam::123456789012:role/MyECSExecutionRole
            #   task_role_arn: arn:aws:iam::123456789012:role/MyECSTaskRole
            #   mount_points:
            #     - sourceVolume: myEfsVolume
            #       containerPath: '/mount/efs'
            #       readOnly: True
            #   volumes:
            #     - name: myEfsVolume
            #       efsVolumeConfiguration:
            #         fileSystemId: fs-1234
            #         rootDirectory: /path/to/my/data
            #   server_sidecar_containers:
            #     - name: DatadogAgent
            #       image: public.ecr.aws/datadog/agent:latest
            #       environment:
            #         - name: ECS_FARGATE
            #           value: true
            #   run_sidecar_containers:
            #     - name: DatadogAgent
            #       image: public.ecr.aws/datadog/agent:latest
            #       environment:
            #         - name: ECS_FARGATE
            #           value: true
            """
        )
    elif agent_platform == DgPlusAgentPlatform.DOCKER:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for Docker resources.
            # docker:
            #   env_vars:
            #     - DATABASE_NAME=staging
            #     - DATABASE_PASSWORD
            """
        )
    else:
        return None


# Template file paths
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent.parent / "templates"
SERVERLESS_GITHUB_ACTION_FILE = TEMPLATES_DIR / "serverless-github-action.yaml"
HYBRID_GITHUB_ACTION_FILE = TEMPLATES_DIR / "hybrid-github-action.yaml"
BUILD_LOCATION_FRAGMENT = TEMPLATES_DIR / "build-location-fragment.yaml"
SERVERLESS_GITLAB_CI_FILE = TEMPLATES_DIR / "serverless-gitlab-ci.yaml"
HYBRID_GITLAB_CI_FILE = TEMPLATES_DIR / "hybrid-gitlab-ci.yaml"
BUILD_LOCATION_FRAGMENT_GITLAB = TEMPLATES_DIR / "build-location-fragment-gitlab.yaml"


class FragmentInfo(NamedTuple):
    """Container registry fragment information for a specific git provider."""

    fragment: Path
    secrets_hints: list[str]


class ContainerRegistryInfo(NamedTuple):
    """Container registry configuration supporting multiple git providers."""

    name: str
    match: Callable[[str], bool]
    github_fragment_info: FragmentInfo
    gitlab_fragment_info: FragmentInfo

    def get_fragment_info(self, provider: GitProvider) -> FragmentInfo:
        """Get the fragment info for the specified git provider."""
        if provider == GitProvider.GITHUB:
            return self.github_fragment_info
        elif provider == GitProvider.GITLAB:
            return self.gitlab_fragment_info
        else:
            raise ValueError(f"Unsupported git provider: {provider}")


def _matches_ecr(url: str) -> bool:
    """Check if URL is an AWS ECR registry.

    ECR URLs follow the format: <account-id>.dkr.ecr.<region>.amazonaws.com
    """
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname or ""
    # Check that hostname ends with .amazonaws.com and contains .ecr. in the subdomain structure
    return hostname.endswith(".amazonaws.com") and ".ecr." in hostname


def _matches_dockerhub(url: str) -> bool:
    """Check if URL is DockerHub."""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname or ""
    return hostname == "docker.io" or hostname.endswith(".docker.io")


def _matches_ghcr(url: str) -> bool:
    """Check if URL is GitHub Container Registry."""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname or ""
    return hostname == "ghcr.io" or hostname.endswith(".ghcr.io")


def _matches_azure(url: str) -> bool:
    """Check if URL is Azure Container Registry.

    Azure URLs follow the format: <name>.azurecr.io
    """
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname or ""
    return hostname == "azurecr.io" or hostname.endswith(".azurecr.io")


def _matches_gcr(url: str) -> bool:
    """Check if URL is Google Container Registry."""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    hostname = parsed.hostname or ""
    return hostname == "gcr.io" or hostname.endswith(".gcr.io")


REGISTRY_INFOS = [
    ContainerRegistryInfo(
        name="ECR",
        match=_matches_ecr,
        github_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR / "registry_fragments" / "github" / "ecr-login-fragment.yaml",
            secrets_hints=[
                'gh secret set AWS_ACCESS_KEY_ID --body "(your AWS access key ID)"',
                'gh secret set AWS_SECRET_ACCESS_KEY --body "(your AWS secret access key)"',
                'gh secret set AWS_REGION --body "(your AWS region)"',
            ],
        ),
        gitlab_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR / "registry_fragments" / "gitlab" / "ecr-login-fragment.yaml",
            secrets_hints=[
                "AWS_ACCESS_KEY_ID - Your AWS access key ID",
                "AWS_SECRET_ACCESS_KEY - Your AWS secret access key",
                "AWS_REGION - Your AWS region",
            ],
        ),
    ),
    ContainerRegistryInfo(
        name="DockerHub",
        match=_matches_dockerhub,
        github_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR
            / "registry_fragments"
            / "github"
            / "dockerhub-login-fragment.yaml",
            secrets_hints=[
                'gh secret set DOCKERHUB_USERNAME --body "(your DockerHub username)"',
                'gh secret set DOCKERHUB_TOKEN --body "(your DockerHub token)"',
            ],
        ),
        gitlab_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR
            / "registry_fragments"
            / "gitlab"
            / "dockerhub-login-fragment.yaml",
            secrets_hints=[
                "DOCKERHUB_USERNAME - Your DockerHub username",
                "DOCKERHUB_TOKEN - Your DockerHub access token",
            ],
        ),
    ),
    ContainerRegistryInfo(
        name="GitHub Container Registry",
        match=_matches_ghcr,
        github_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR
            / "registry_fragments"
            / "github"
            / "github-container-registry-login-fragment.yaml",
            secrets_hints=[],
        ),
        gitlab_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR
            / "registry_fragments"
            / "gitlab"
            / "github-container-registry-login-fragment.yaml",
            secrets_hints=[
                "GITHUB_USERNAME - Your GitHub username",
                "GITHUB_TOKEN - Your GitHub personal access token with packages:read permission",
            ],
        ),
    ),
    ContainerRegistryInfo(
        name="Azure Container Registry",
        match=_matches_azure,
        github_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR
            / "registry_fragments"
            / "github"
            / "azure-container-registry-login-fragment.yaml",
            secrets_hints=[
                'gh secret set AZURE_CLIENT_ID --body "(your Azure client ID)"',
                'gh secret set AZURE_CLIENT_SECRET --body "(your Azure client secret)"',
            ],
        ),
        gitlab_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR
            / "registry_fragments"
            / "gitlab"
            / "azure-container-registry-login-fragment.yaml",
            secrets_hints=[
                "AZURE_CLIENT_ID - Your Azure service principal client ID",
                "AZURE_CLIENT_SECRET - Your Azure service principal client secret",
            ],
        ),
    ),
    ContainerRegistryInfo(
        name="Google Container Registry",
        match=_matches_gcr,
        github_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR / "registry_fragments" / "github" / "gcr-login-fragment.yaml",
            secrets_hints=[
                'gh secret set GCR_JSON_KEY --body "(your GCR JSON key)"',
            ],
        ),
        gitlab_fragment_info=FragmentInfo(
            fragment=TEMPLATES_DIR / "registry_fragments" / "gitlab" / "gcr-login-fragment.yaml",
            secrets_hints=[
                "GCR_JSON_KEY - Your GCR service account JSON key",
            ],
        ),
    ),
]


def _build_ecr_url(account_id: str, region: str, repo_name: str) -> str:
    """Build an AWS ECR registry URL."""
    return f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}"


def _build_gcr_url(project_id: str, image_name: str) -> str:
    """Build a Google Container Registry URL."""
    return f"gcr.io/{project_id}/{image_name}"


def _build_azure_acr_url(registry_name: str, image_name: str) -> str:
    """Build an Azure Container Registry URL."""
    return f"{registry_name}.azurecr.io/{image_name}"


def _build_dockerhub_url(username: str, repo_name: str) -> str:
    """Build a DockerHub registry URL."""
    return f"docker.io/{username}/{repo_name}"


def _build_ghcr_url(owner: str, image_name: str) -> str:
    """Build a GitHub Container Registry URL."""
    return f"ghcr.io/{owner}/{image_name}"


def _prompt_for_ecr_details() -> str:
    """Prompt for ECR registry details and return the constructed URL."""
    import click

    account_id = click.prompt("AWS Account ID (12-digit number)")
    region = click.prompt("AWS Region", default="us-east-1")
    repo_name = click.prompt("Repository name")
    return _build_ecr_url(account_id, region, repo_name)


def _prompt_for_gcr_details() -> str:
    """Prompt for GCR registry details and return the constructed URL."""
    import click

    project_id = click.prompt("GCP Project ID")
    image_name = click.prompt("Image name")
    return _build_gcr_url(project_id, image_name)


def _prompt_for_azure_acr_details() -> str:
    """Prompt for Azure ACR registry details and return the constructed URL."""
    import click

    registry_name = click.prompt("Azure Container Registry name (without .azurecr.io)")
    image_name = click.prompt("Image name")
    return _build_azure_acr_url(registry_name, image_name)


def _prompt_for_dockerhub_details() -> str:
    """Prompt for DockerHub registry details and return the constructed URL."""
    import click

    username = click.prompt("DockerHub username or organization")
    repo_name = click.prompt("Repository name")
    return _build_dockerhub_url(username, repo_name)


def _prompt_for_ghcr_details() -> str:
    """Prompt for GHCR registry details and return the constructed URL."""
    import click

    owner = click.prompt("GitHub owner (username or organization)")
    image_name = click.prompt("Image name")
    return _build_ghcr_url(owner, image_name)


def prompt_for_registry_url(skip_prompt: bool = False) -> Optional[str]:
    """Prompt user to configure container registry URL with interactive options.

    Args:
        skip_prompt: If True, skip the prompt and return None (keeping placeholder).

    Returns:
        The registry URL if provided, or None if skipped.
    """
    import click

    if skip_prompt:
        return None

    click.echo("\nConfigure container registry for Docker image storage:")
    click.echo("  [1] AWS ECR")
    click.echo("  [2] Google Container Registry (GCR)")
    click.echo("  [3] Azure Container Registry")
    click.echo("  [4] DockerHub")
    click.echo("  [5] GitHub Container Registry (GHCR)")
    click.echo("  [6] Enter URL directly")
    click.echo("  [7] Skip (configure later)")

    choice = click.prompt(
        "\nRegistry type",
        type=click.Choice(["1", "2", "3", "4", "5", "6", "7"]),
        default="7",
    )

    if choice == "1":
        return _prompt_for_ecr_details()
    elif choice == "2":
        return _prompt_for_gcr_details()
    elif choice == "3":
        return _prompt_for_azure_acr_details()
    elif choice == "4":
        return _prompt_for_dockerhub_details()
    elif choice == "5":
        return _prompt_for_ghcr_details()
    elif choice == "6":
        click.echo("\nExamples:")
        click.echo("  ECR:       123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo")
        click.echo("  GCR:       gcr.io/my-project/my-image")
        click.echo("  Azure:     myregistry.azurecr.io/my-image")
        click.echo("  DockerHub: docker.io/myuser/my-image")
        click.echo("  GHCR:      ghcr.io/myorg/my-image")
        return click.prompt("\nRegistry URL")
    else:  # choice == "7"
        return None


def get_registry_info_for_url(registry_url: str) -> Optional[ContainerRegistryInfo]:
    """Get the ContainerRegistryInfo for a given registry URL.

    Args:
        registry_url: The registry URL to match.

    Returns:
        The matching ContainerRegistryInfo, or None if no match found.
    """
    for registry_info in REGISTRY_INFOS:
        if registry_info.match(registry_url):
            return registry_info
    return None


def display_registry_secrets_hints(
    registry_url: Optional[str], git_provider: Optional[GitProvider]
) -> None:
    """Display required CI/CD secrets for the detected registry type.

    Args:
        registry_url: The registry URL to detect type from.
        git_provider: The git provider (GitHub or GitLab) for provider-specific hints.
    """
    import click

    if not registry_url or registry_url == "...":
        return

    if not git_provider:
        return

    registry_info = get_registry_info_for_url(registry_url)
    if not registry_info:
        click.echo(
            f"\nNote: Could not detect registry type for '{registry_url}'. "
            "You may need to configure CI/CD secrets manually."
        )
        return

    fragment_info = registry_info.get_fragment_info(git_provider)
    if not fragment_info.secrets_hints:
        # Some registries (like GHCR on GitHub) don't need additional secrets
        click.echo(f"\nRegistry '{registry_info.name}' detected. No additional secrets required.")
        return

    provider_name = "GitHub" if git_provider == GitProvider.GITHUB else "GitLab"
    click.echo(
        f"\nTo enable CI/CD with {registry_info.name}, configure these {provider_name} secrets:"
    )
    for hint in fragment_info.secrets_hints:
        click.echo(f"  {hint}")
