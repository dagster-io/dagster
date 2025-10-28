"""Shared utilities for CI scaffolding commands (GitHub Actions, GitLab CI, etc.)."""

from pathlib import Path
from typing import Optional, cast

import click
from dagster_dg_core.config import DgRawCliConfig, normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import exit_with_error
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.utils.plus.build import get_agent_type, get_dockerfile_path, merge_build_configs


def get_cli_version_or_main() -> str:
    """Get CLI version string for CI workflows.

    Returns:
        "main" for development versions, "vX.Y.Z" for releases
    """
    from dagster_dg_cli.version import __version__ as cli_version

    return "main" if cli_version.endswith("+dev") else f"v{cli_version}"


def search_for_git_root(path: Path) -> Optional[Path]:
    """Recursively search for git repository root.

    Args:
        path: Starting path to search from

    Returns:
        Path to git root if found, None otherwise
    """
    if path.joinpath(".git").exists():
        return path
    elif path.parent == path:
        return None
    else:
        return search_for_git_root(path.parent)


def get_project_contexts(dg_context: DgContext, cli_config: DgRawCliConfig) -> list[DgContext]:
    """Get list of project contexts from workspace or single project.

    Args:
        dg_context: The current Dagster context
        cli_config: CLI configuration

    Returns:
        List of project contexts. For workspaces, returns all projects.
        For standalone projects, returns single-item list.
    """
    if dg_context.is_in_workspace:
        return [
            dg_context.for_project_environment(project.path, cli_config)
            for project in dg_context.project_specs
        ]
    else:
        return [dg_context]


class CIScaffoldConfig:
    """Configuration gathered for CI scaffolding.

    This class holds all the common configuration needed to scaffold
    CI workflows across different platforms (GitHub Actions, GitLab CI, etc.)
    """

    def __init__(
        self,
        git_root: Path,
        dg_context: DgContext,
        organization_name: str,
        deployment_name: str,
        agent_type: DgPlusAgentType,
    ):
        self.git_root = git_root
        self.dg_context = dg_context
        self.organization_name = organization_name
        self.deployment_name = deployment_name
        self.agent_type = agent_type


def gather_ci_config(
    git_root: Optional[Path],
    global_options: object,
    click_context,
) -> CIScaffoldConfig:
    """Gather common configuration for CI scaffolding.

    This function handles all the common setup logic shared across CI platforms:
    - Git root detection and validation
    - Config loading (Plus config, CLI config)
    - Organization/deployment name prompting (with defaults from config)
    - Agent type detection (serverless vs hybrid)

    Args:
        git_root: Optional explicit git root path
        global_options: Global CLI options
        click_context: Click context

    Returns:
        CIScaffoldConfig with all gathered configuration

    Raises:
        SystemExit: If no git repository found
    """
    # Git root detection
    git_root = git_root or search_for_git_root(Path.cwd())
    if git_root is None:
        exit_with_error(
            "No git repository found. CI scaffolding must be run from a git repository, or "
            "specify the path to the git root with `--git-root`."
        )

    # Context loading
    cli_config = normalize_cli_config(global_options, click_context)
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)
    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    # Organization name
    if plus_config and plus_config.organization:
        organization_name = plus_config.organization
        click.echo(f"Using organization name {organization_name} from Dagster Plus config.")
    else:
        organization_name = click.prompt("Dagster Plus organization name") or ""

    # Deployment name
    if plus_config and plus_config.default_deployment:
        deployment_name = plus_config.default_deployment
        click.echo(f"Using default deployment name {deployment_name} from Dagster Plus config.")
    else:
        deployment_name = click.prompt("Default deployment name", default="prod")

    # Agent type
    agent_type = get_agent_type(plus_config)
    if agent_type == DgPlusAgentType.SERVERLESS:
        click.echo("Using serverless workflow template.")
    else:
        click.echo("Using hybrid workflow template.")

    return CIScaffoldConfig(
        git_root=git_root,
        dg_context=dg_context,
        organization_name=organization_name,
        deployment_name=deployment_name,
        agent_type=agent_type,
    )


def apply_template_replacements(
    template: str,
    config: CIScaffoldConfig,
) -> str:
    """Apply common template replacements.

    Replaces standard placeholders used across all CI platforms:
    - TEMPLATE_ORGANIZATION_NAME
    - TEMPLATE_DEFAULT_DEPLOYMENT_NAME
    - TEMPLATE_PROJECT_DIR
    - TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION

    Args:
        template: Template string with placeholders
        config: CI scaffold configuration

    Returns:
        Template with placeholders replaced
    """
    return (
        template.replace("TEMPLATE_ORGANIZATION_NAME", config.organization_name)
        .replace("TEMPLATE_DEFAULT_DEPLOYMENT_NAME", config.deployment_name)
        .replace(
            "TEMPLATE_PROJECT_DIR", str(config.dg_context.root_path.relative_to(config.git_root))
        )
        .replace("TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION", get_cli_version_or_main())
    )


def validate_hybrid_build_config(
    config: CIScaffoldConfig,
    cli_config: DgRawCliConfig,
) -> tuple[list[DgContext], list[str]]:
    """Validate hybrid deployment build configuration.

    Performs validation for hybrid deployments:
    1. Extracts project contexts
    2. Validates registry URLs are configured
    3. Validates Dockerfiles exist for all locations

    Args:
        config: CI scaffold configuration
        cli_config: CLI configuration

    Returns:
        Tuple of (project_contexts, registry_urls)

    Raises:
        click.ClickException: If validation fails (missing registry or Dockerfile)
    """
    project_contexts = get_project_contexts(config.dg_context, cli_config)

    # Extract and validate registry URLs
    registry_urls = [
        merge_build_configs(project.build_config, config.dg_context.build_config).get("registry")
        for project in project_contexts
    ]
    for project, registry_url in zip(project_contexts, registry_urls):
        if registry_url is None:
            raise click.ClickException(
                f"No registry URL found for project {project.code_location_name}. "
                f"Please specify a registry URL in `build.yaml`."
            )
    registry_urls = cast("list[str]", registry_urls)

    # Validate Dockerfiles exist
    for location_ctx in project_contexts:
        dockerfile_path = get_dockerfile_path(location_ctx, config.dg_context)
        if not dockerfile_path.exists():
            raise click.ClickException(
                f"Dockerfile not found at {dockerfile_path}. "
                f"Please run `dg scaffold build-artifacts` in {location_ctx.root_path} to create one."
            )

    return project_contexts, registry_urls
