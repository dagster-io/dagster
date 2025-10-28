import subprocess
from pathlib import Path
from typing import Callable, NamedTuple, Optional, cast

import click
from dagster_dg_core.config import DgRawCliConfig, normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand, exit_with_error
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.utils.plus.build import get_agent_type, get_dockerfile_path, merge_build_configs


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


def _get_project_contexts(dg_context: DgContext, cli_config: DgRawCliConfig) -> list[DgContext]:
    if dg_context.is_in_workspace:
        return [
            dg_context.for_project_environment(project.path, cli_config)
            for project in dg_context.project_specs
        ]
    else:
        return [dg_context]


def _get_git_web_url(git_root: Path) -> Optional[str]:
    try:
        # Try to get the GitLab remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=git_root,
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        # Convert SSH URL to HTTPS if needed
        if remote_url.startswith("git@gitlab.com:"):
            remote_url = remote_url.replace("git@gitlab.com:", "https://gitlab.com/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]

        return remote_url
    except subprocess.CalledProcessError:
        return None


# Template file paths
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
SERVERLESS_GITLAB_CI_FILE = TEMPLATES_DIR / "serverless-gitlab-ci.yml"
HYBRID_GITLAB_CI_FILE = TEMPLATES_DIR / "hybrid-gitlab-ci.yml"

BUILD_LOCATION_FRAGMENT = TEMPLATES_DIR / "build-location-fragment-gitlab.yml"


class ContainerRegistryInfo(NamedTuple):
    name: str
    match: Callable[[str], bool]
    fragment: Path
    secrets_hints: list[str]


REGISTRY_INFOS = [
    ContainerRegistryInfo(
        name="ECR",
        match=lambda url: "ecr" in url,
        fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "ecr-login-fragment.yml",
        secrets_hints=[
            "AWS_ACCESS_KEY_ID - Your AWS access key ID",
            "AWS_SECRET_ACCESS_KEY - Your AWS secret access key",
            "AWS_REGION - Your AWS region (e.g., us-east-1)",
        ],
    ),
    ContainerRegistryInfo(
        name="DockerHub",
        match=lambda url: "docker.io" in url,
        fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "dockerhub-login-fragment.yml",
        secrets_hints=[
            "DOCKERHUB_USERNAME - Your DockerHub username",
            "DOCKERHUB_TOKEN - Your DockerHub access token",
        ],
    ),
    ContainerRegistryInfo(
        name="GitLab Container Registry",
        match=lambda url: "registry.gitlab.com" in url or "gitlab.com" in url,
        fragment=TEMPLATES_DIR
        / "gitlab_registry_fragments"
        / "gitlab-container-registry-login-fragment.yml",
        secrets_hints=[],
    ),
    ContainerRegistryInfo(
        name="Azure Container Registry",
        match=lambda url: "azurecr.io" in url,
        fragment=TEMPLATES_DIR
        / "gitlab_registry_fragments"
        / "azure-container-registry-login-fragment.yml",
        secrets_hints=[
            "AZURE_CLIENT_ID - Your Azure client ID",
            "AZURE_CLIENT_SECRET - Your Azure client secret",
            "AZURE_TENANT_ID - Your Azure tenant ID",
        ],
    ),
    ContainerRegistryInfo(
        name="Google Container Registry",
        match=lambda url: "gcr.io" in url,
        fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "gcr-login-fragment.yml",
        secrets_hints=[
            "GCR_JSON_KEY - Your GCR service account JSON key",
        ],
    ),
]


def _get_build_fragment_for_locations(
    location_ctxs: list[DgContext], git_root: Path, registry_urls: list[str]
) -> str:
    output = []
    for location_ctx, registry_url in zip(location_ctxs, registry_urls):
        # Get the registry login fragment for this registry
        registry_fragment = ""
        for registry_info in REGISTRY_INFOS:
            if registry_info.match(registry_url):
                registry_fragment = registry_info.fragment.read_text()
                if "TEMPLATE_IMAGE_REGISTRY" in registry_fragment:
                    registry_fragment = registry_fragment.replace(
                        "TEMPLATE_IMAGE_REGISTRY", registry_url
                    )
                break

        # Build the job definition
        job_content = (
            BUILD_LOCATION_FRAGMENT.read_text()
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace("TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(git_root)))
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
            .replace("    # TEMPLATE_REGISTRY_LOGIN_FRAGMENT", registry_fragment)
        )
        output.append(job_content)
    return "\n".join(output)


def _get_registry_fragment(registry_urls: list[str]) -> tuple[str, list[str]]:
    additional_secrets_hints = []
    seen_registries = set()

    for registry_url in registry_urls:
        for registry_info in REGISTRY_INFOS:
            if registry_info.match(registry_url) and registry_info.name not in seen_registries:
                seen_registries.add(registry_info.name)
                additional_secrets_hints.extend(registry_info.secrets_hints)
                break

    return "", additional_secrets_hints


@click.command(
    name="gitlab-ci",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@dg_global_options
@cli_telemetry_wrapper
def scaffold_gitlab_ci_command(git_root: Optional[Path], **global_options: object) -> None:
    """Scaffold GitLab CI configuration for a Dagster project.

    This command will create a .gitlab-ci.yml file in the repository root.
    """
    import typer

    git_root = git_root or search_for_git_root(Path.cwd())
    if git_root is None:
        exit_with_error(
            "No git repository found. `dg scaffold gitlab-ci` must be run from a git repository, or "
            "specify the path to the git root with `--git-root`."
        )

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    if plus_config and plus_config.organization:
        organization_name = plus_config.organization
        click.echo(f"Using organization name {organization_name} from Dagster Plus config.")
    else:
        organization_name = click.prompt("Dagster Plus organization name") or ""

    if plus_config and plus_config.default_deployment:
        deployment_name = plus_config.default_deployment
        click.echo(f"Using default deployment name {deployment_name} from Dagster Plus config.")
    else:
        deployment_name = click.prompt("Default deployment name", default="prod")

    agent_type = get_agent_type(plus_config)
    if agent_type == DgPlusAgentType.SERVERLESS:
        click.echo("Using serverless workflow template.")
    else:
        click.echo("Using hybrid workflow template.")

    additional_secrets_hints = []

    template = (
        SERVERLESS_GITLAB_CI_FILE.read_text()
        if agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITLAB_CI_FILE.read_text()
    )

    template = (
        template.replace(
            "TEMPLATE_ORGANIZATION_NAME",
            organization_name,
        )
        .replace(
            "TEMPLATE_DEFAULT_DEPLOYMENT_NAME",
            deployment_name,
        )
        .replace(
            "TEMPLATE_PROJECT_DIR",
            str(dg_context.root_path.relative_to(git_root)),
        )
        .replace(
            "TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION",
            get_cli_version_or_main(),
        )
    )

    registry_urls = None
    if agent_type == DgPlusAgentType.HYBRID:
        project_contexts = _get_project_contexts(dg_context, cli_config)

        registry_urls = [
            merge_build_configs(project.build_config, dg_context.build_config).get("registry")
            for project in project_contexts
        ]
        for project, registry_url in zip(project_contexts, registry_urls):
            if registry_url is None:
                raise click.ClickException(
                    f"No registry URL found for project {project.code_location_name}. Please specify a registry URL in `build.yaml`."
                )
        registry_urls = cast("list[str]", registry_urls)

        for location_ctx in project_contexts:
            dockerfile_path = get_dockerfile_path(location_ctx, dg_context)
            if not dockerfile_path.exists():
                raise click.ClickException(
                    f"Dockerfile not found at {dockerfile_path}. Please run `dg scaffold build-artifacts` in {location_ctx.root_path} to create one."
                )

        build_fragment = _get_build_fragment_for_locations(
            project_contexts, git_root, registry_urls
        )
        template = template.replace("# TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        _, additional_secrets_hints = _get_registry_fragment(registry_urls)

    gitlab_ci_file = git_root / ".gitlab-ci.yml"
    gitlab_ci_file.write_text(template)

    git_web_url = _get_git_web_url(git_root) or ""
    if git_web_url:
        git_web_url = f"({git_web_url}/-/settings/ci_cd) "

    click.echo(
        typer.style(
            "\nGitLab CI configuration created successfully. Commit and push your changes to deploy to Dagster Plus.\n",
            fg=typer.colors.GREEN,
        )
        + f"\nYou will need to set up the following CI/CD variables in your GitLab project\n(Settings > CI/CD > Variables) {git_web_url}:"
        + typer.style(
            f"\n\nDAGSTER_CLOUD_API_TOKEN - Create using:\n  dg plus create ci-api-token --description 'Used in {git_root.name} GitLab CI'"
            + ("\n\n" + "\n".join(additional_secrets_hints) if additional_secrets_hints else ""),
            fg=typer.colors.YELLOW,
        )
    )
