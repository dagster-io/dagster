import subprocess
import textwrap
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
    from dagster_cloud_cli.core.pex_builder.code_location import get_local_repo_name

    try:
        local_repo_name = get_local_repo_name(str(git_root))
        return f"https://github.com/{local_repo_name}"
    except subprocess.CalledProcessError:
        return None


# Template file paths
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
SERVERLESS_GITHUB_ACTION_FILE = TEMPLATES_DIR / "serverless-github-action.yaml"
HYBRID_GITHUB_ACTION_FILE = TEMPLATES_DIR / "hybrid-github-action.yaml"

BUILD_LOCATION_FRAGMENT = TEMPLATES_DIR / "build-location-fragment.yaml"


class ContainerRegistryInfo(NamedTuple):
    name: str
    match: Callable[[str], bool]
    fragment: Path
    secrets_hints: list[str]


REGISTRY_INFOS = [
    ContainerRegistryInfo(
        name="ECR",
        match=lambda url: "ecr" in url,
        fragment=TEMPLATES_DIR / "registry_fragments" / "ecr-login-fragment.yaml",
        secrets_hints=[
            'gh secret set AWS_ACCESS_KEY_ID --body "(your AWS access key ID)"',
            'gh secret set AWS_SECRET_ACCESS_KEY --body "(your AWS secret access key)"',
            'gh secret set AWS_REGION --body "(your AWS region)"',
        ],
    ),
    ContainerRegistryInfo(
        name="DockerHub",
        match=lambda url: "docker.io" in url,
        fragment=TEMPLATES_DIR / "registry_fragments" / "dockerhub-login-fragment.yaml",
        secrets_hints=[
            'gh secret set DOCKERHUB_USERNAME --body "(your DockerHub username)"',
            'gh secret set DOCKERHUB_TOKEN --body "(your DockerHub token)"',
        ],
    ),
    ContainerRegistryInfo(
        name="GitHub Container Registry",
        match=lambda url: "ghcr.io" in url,
        fragment=TEMPLATES_DIR
        / "registry_fragments"
        / "github-container-registry-login-fragment.yaml",
        secrets_hints=[],
    ),
    ContainerRegistryInfo(
        name="Azure Container Registry",
        match=lambda url: "azurecr.io" in url,
        fragment=TEMPLATES_DIR
        / "registry_fragments"
        / "azure-container-registry-login-fragment.yaml",
        secrets_hints=[
            'gh secret set AZURE_CLIENT_ID --body "(your Azure client ID)"',
            'gh secret set AZURE_CLIENT_SECRET --body "(your Azure client secret)"',
        ],
    ),
    ContainerRegistryInfo(
        name="Google Container Registry",
        match=lambda url: "gcr.io" in url,
        fragment=TEMPLATES_DIR / "registry_fragments" / "gcr-login-fragment.yaml",
        secrets_hints=[
            'gh secret set GCR_JSON_KEY --body "(your GCR JSON key)"',
        ],
    ),
]


def _get_build_fragment_for_locations(
    location_ctxs: list[DgContext], git_root: Path, registry_urls: list[str]
) -> str:
    # TODO: when we cut over to dg deploy, we'll just use a single build call for the workspace
    # rather than iterating over each project
    output = []
    for location_ctx, registry_url in zip(location_ctxs, registry_urls):
        output.append(
            textwrap.indent(BUILD_LOCATION_FRAGMENT.read_text(), " " * 6)
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace("TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(git_root)))
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
            .replace("TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION", get_cli_version_or_main())
        )
    return "\n" + "\n".join(output)


def _get_registry_fragment(registry_urls: list[str]) -> tuple[str, list[str]]:
    additional_secrets_hints = []
    output = []
    for registry_info in REGISTRY_INFOS:
        fragment = registry_info.fragment.read_text()
        matching_urls = [url for url in registry_urls if registry_info.match(url)]
        if matching_urls:
            if "TEMPLATE_IMAGE_REGISTRY" not in fragment:
                output.append(fragment)
            else:
                for url in matching_urls:
                    output.append(fragment.replace("TEMPLATE_IMAGE_REGISTRY", url))
            additional_secrets_hints.extend(registry_info.secrets_hints)

    return "\n".join(output), additional_secrets_hints


@click.command(
    name="github-actions",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@dg_global_options
@cli_telemetry_wrapper
def scaffold_github_actions_command(git_root: Optional[Path], **global_options: object) -> None:
    """Scaffold a GitHub Actions workflow for a Dagster project.

    This command will create a GitHub Actions workflow in the `.github/workflows` directory.
    """
    import typer

    git_root = git_root or search_for_git_root(Path.cwd())
    if git_root is None:
        exit_with_error(
            "No git repository found. `dg scaffold github-actions` must be run from a git repository, or "
            "specify the path to the git root with `--git-root`."
        )

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    workflows_dir = git_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

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
        SERVERLESS_GITHUB_ACTION_FILE.read_text()
        if agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITHUB_ACTION_FILE.read_text()
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
        template = template.replace("      # TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        registry_fragment, additional_secrets_hints = _get_registry_fragment(registry_urls)
        template = template.replace(
            "# TEMPLATE_CONTAINER_REGISTRY_LOGIN_FRAGMENT",
            textwrap.indent(
                registry_fragment,
                " " * 6,
            ),
        )

    workflow_file = workflows_dir / "dagster-plus-deploy.yml"
    workflow_file.write_text(template)

    git_web_url = _get_git_web_url(git_root) or ""
    if git_web_url:
        git_web_url = f"({git_web_url}/settings/secrets/actions) "
    click.echo(
        typer.style(
            "\nGitHub Actions workflow created successfully. Commit and push your changes in order to deploy to Dagster Plus.\n",
            fg=typer.colors.GREEN,
        )
        + f"\nYou will need to set up the following secrets in your GitHub repository using\nthe GitHub UI {git_web_url}or CLI (https://cli.github.com/):"
        + typer.style(
            f"\ndg plus create ci-api-token --description 'Used in {git_root.name} GitHub Actions' | gh secret set DAGSTER_CLOUD_API_TOKEN"
            + "\n"
            + "\n".join(additional_secrets_hints),
            fg=typer.colors.YELLOW,
        )
    )
