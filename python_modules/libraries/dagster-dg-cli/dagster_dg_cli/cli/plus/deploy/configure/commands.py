"""Primary interface for deployment configuration scaffolding.

This module provides the `dg scaffold deployment-config` command group with
subcommands for serverless and hybrid deployments.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_editable_dagster_options, dg_global_options
from dagster_dg_core.utils import DgClickCommand, DgClickGroup, exit_with_error
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform, DgPlusAgentType
from dagster_dg_cli.cli.plus.deploy.configure.configure_build_artifacts import (
    configure_build_artifacts_impl,
)
from dagster_dg_cli.cli.plus.deploy.configure.configure_ci import configure_ci_impl
from dagster_dg_cli.cli.plus.deploy.configure.utils import (
    DgPlusDeployConfigureOptions,
    GitProvider,
    detect_agent_type_and_platform,
    search_for_git_root,
)


def resolve_agent_type_and_platform(
    agent_type: Optional[DgPlusAgentType],
    agent_platform: Optional[DgPlusAgentPlatform],
    plus_config: Optional[DagsterPlusCliConfig],
) -> tuple[DgPlusAgentType, Optional[DgPlusAgentPlatform]]:
    """Resolve agent type and platform from config or prompts (for deployment-config commands)."""
    resolved_type = agent_type
    resolved_platform = agent_platform

    # Try to detect from Plus config via GraphQL
    if resolved_type is None and plus_config:
        detected_type, detected_platform = detect_agent_type_and_platform(plus_config)
        resolved_type = detected_type
        if resolved_platform is None:
            resolved_platform = detected_platform

    # Prompt for agent type if still missing
    if resolved_type is None:
        resolved_type = DgPlusAgentType(
            click.prompt(
                "Deployment agent type",
                type=click.Choice(["serverless", "hybrid"]),
            ).upper()
        )

    # Prompt for platform if needed (only for hybrid)
    if resolved_type == DgPlusAgentType.HYBRID and resolved_platform is None:
        resolved_platform = DgPlusAgentPlatform(
            click.prompt(
                "Agent platform",
                type=click.Choice(["k8s", "ecs", "docker"]),
            ).upper()
        )

    return resolved_type, resolved_platform


def resolve_organization(
    organization: Optional[str],
    plus_config: Optional[DagsterPlusCliConfig],
    *,
    show_detected_message: bool = True,
) -> Optional[str]:
    """Resolve organization name from config or prompt."""
    if organization is not None:
        return organization

    if plus_config and plus_config.organization:
        if show_detected_message:
            click.echo(
                f"Using organization name {plus_config.organization} from Dagster Plus config."
            )
        return plus_config.organization

    return click.prompt("Dagster Plus organization name") or ""


def resolve_deployment(
    deployment: Optional[str],
    plus_config: Optional[DagsterPlusCliConfig],
    *,
    show_detected_message: bool = True,
) -> str:
    """Resolve deployment name from config or prompt."""
    if deployment is not None:
        return deployment

    if plus_config and plus_config.default_deployment:
        if show_detected_message:
            click.echo(
                f"Using default deployment name {plus_config.default_deployment} from Dagster Plus config."
            )
        return plus_config.default_deployment

    return click.prompt("Default deployment name", default="prod")


def resolve_git_provider(
    git_provider: Optional[GitProvider],
    git_root: Optional[Path],
) -> Optional[GitProvider]:
    """Resolve git provider for CI/CD scaffolding (for deployment-config commands)."""
    if git_provider is not None:
        return git_provider

    # Prompt for CI/CD configuration
    if git_root is None:
        should_scaffold_ci = click.confirm(
            "Would you like to scaffold CI/CD configuration?", default=True
        )
        if should_scaffold_ci:
            provider_choice = click.prompt(
                "Git provider",
                type=click.Choice(["github", "gitlab"]),
                default="github",
            )
            return GitProvider(provider_choice)

    return None


def resolve_git_root(
    git_root: Optional[Path],
    git_provider: Optional[GitProvider],
) -> Optional[Path]:
    """Resolve git root path."""
    if git_provider is None:
        return None

    if git_root is not None:
        return git_root

    resolved_git_root = search_for_git_root(Path.cwd())
    if resolved_git_root is None:
        exit_with_error(
            "No git repository found. Must be run from a git repository, or "
            "specify the path to the git root with `--git-root`."
        )

    return resolved_git_root


def resolve_python_version(python_version: Optional[str]) -> str:
    """Resolve Python version."""
    return python_version or f"3.{sys.version_info.minor}"


def _resolve_config_with_prompts(
    agent_type: Optional[DgPlusAgentType],
    agent_platform: Optional[DgPlusAgentPlatform],
    organization: Optional[str],
    deployment: Optional[str],
    git_root: Optional[Path],
    python_version: Optional[str],
    skip_confirmation_prompt: bool,
    use_editable_dagster: bool,
    git_provider: Optional[GitProvider],
    dg_context: DgContext,
    cli_config,
    pex_deploy: Optional[bool] = None,
    registry_url: Optional[str] = None,
) -> DgPlusDeployConfigureOptions:
    """Resolve all configuration for deployment-config commands, prompting for missing values.

    This is used by the primary deployment-config commands (serverless/hybrid).
    For legacy commands, use the specialized resolve functions below.
    """
    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    # Resolve agent type and platform
    resolved_agent_type, resolved_agent_platform = resolve_agent_type_and_platform(
        agent_type,
        agent_platform,
        plus_config,
    )

    # Resolve git provider
    resolved_git_provider = resolve_git_provider(
        git_provider,
        git_root,
    )

    # Resolve organization and deployment (only needed if scaffolding CI/CD)
    resolved_organization = None
    resolved_deployment = deployment or "prod"
    if resolved_git_provider is not None:
        resolved_organization = resolve_organization(organization, plus_config)
        resolved_deployment = resolve_deployment(deployment, plus_config)

    # Resolve git root
    resolved_git_root = resolve_git_root(git_root, resolved_git_provider)

    # Resolve Python version (required for both serverless and hybrid Dockerfile creation)
    resolved_python_version = resolve_python_version(python_version)

    # Resolve pex_deploy for serverless (prompt if not provided)
    resolved_pex_deploy = None
    if resolved_agent_type == DgPlusAgentType.SERVERLESS:
        if pex_deploy is None:
            resolved_pex_deploy = click.confirm(
                "Enable PEX-based fast deploys?",
                default=True,
            )
        else:
            resolved_pex_deploy = pex_deploy

    return DgPlusDeployConfigureOptions(
        dg_context=dg_context,
        cli_config=cli_config,
        plus_config=plus_config,
        agent_type=resolved_agent_type,
        agent_platform=resolved_agent_platform,
        organization_name=resolved_organization,
        deployment_name=resolved_deployment,
        git_root=resolved_git_root,
        python_version=resolved_python_version,
        skip_confirmation_prompt=skip_confirmation_prompt,
        git_provider=resolved_git_provider,
        use_editable_dagster=use_editable_dagster,
        pex_deploy=resolved_pex_deploy,
        registry_url=registry_url,
    )


# ########################
# ##### CLI COMMANDS
# ########################


@click.group(name="configure", cls=DgClickGroup, invoke_without_command=True)
@click.option(
    "--git-provider",
    type=click.Choice(["github", "gitlab"]),
    help="Git provider for CI/CD scaffolding",
)
@dg_global_options
@cli_telemetry_wrapper
@click.pass_context
def deploy_configure_group(
    ctx: click.Context,
    git_provider: Optional[str],
    **global_options: object,
) -> None:
    """Scaffold deployment configuration files for Dagster Plus.

    If no subcommand is specified, will attempt to auto-detect the agent type from your
    Dagster Plus deployment. If detection fails, you will be prompted to choose between
    serverless or hybrid.

    If run in a `workspace <https://docs.dagster.io/guides/build/projects/workspaces/creating-workspaces>`__,
    will scaffold configuration files for the workspace and all projects contained in it.
    """
    # If a subcommand was invoked, let Click handle it
    if ctx.invoked_subcommand is not None:
        return

    cli_config = normalize_cli_config(global_options, ctx)
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    # Resolve all configuration via prompts and auto-detection
    config = _resolve_config_with_prompts(
        agent_type=None,
        agent_platform=None,
        organization=None,
        deployment=None,
        git_root=None,
        python_version=None,
        skip_confirmation_prompt=False,
        use_editable_dagster=False,
        git_provider=GitProvider(git_provider) if git_provider else None,
        dg_context=dg_context,
        cli_config=cli_config,
        pex_deploy=None,
    )

    configure_build_artifacts_impl(config)
    configure_ci_impl(config)


@click.command(name="serverless", cls=DgClickCommand)
@click.option(
    "--git-provider",
    type=click.Choice(["github", "gitlab"]),
    help="Git provider for CI/CD scaffolding",
)
@click.option(
    "--python-version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12", "3.13"]),
    help="Python version used to deploy the project",
)
@click.option(
    "--organization",
    help="Dagster Plus organization name",
)
@click.option(
    "--deployment",
    default="prod",
    help="Deployment name",
)
@click.option(
    "--git-root",
    type=Path,
    help="Path to the git repository root",
)
@click.option(
    "--pex-deploy/--no-pex-deploy",
    default=True,
    help="Enable PEX-based fast deploys (default: True). If disabled, Docker builds will be used.",
)
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts",
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def deploy_configure_serverless(
    git_provider: Optional[str],
    python_version: Optional[str],
    organization: Optional[str],
    deployment: Optional[str],
    git_root: Optional[Path],
    pex_deploy: bool,
    skip_confirmation_prompt: bool,
    use_editable_dagster: Optional[str],
    **global_options: object,
) -> None:
    """Scaffold deployment configuration for Dagster Plus Serverless.

    This creates:
    - Required files for CI/CD based on your Git provider (GitHub Actions or GitLab CI)
    - Dockerfile and build.yaml for containerization (if --no-pex-deploy is used)
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    config = _resolve_config_with_prompts(
        agent_type=DgPlusAgentType.SERVERLESS,
        agent_platform=None,
        organization=organization,
        deployment=deployment,
        git_root=git_root,
        python_version=python_version,
        skip_confirmation_prompt=skip_confirmation_prompt,
        use_editable_dagster=bool(use_editable_dagster),
        git_provider=GitProvider(git_provider) if git_provider else None,
        dg_context=dg_context,
        cli_config=cli_config,
        pex_deploy=pex_deploy,
    )

    configure_build_artifacts_impl(config)
    configure_ci_impl(config)


@click.command(name="hybrid", cls=DgClickCommand)
@click.option(
    "--git-provider",
    type=click.Choice(["github", "gitlab"]),
    help="Git provider for CI/CD scaffolding",
)
@click.option(
    "--agent-platform",
    type=click.Choice(["k8s", "ecs", "docker"]),
    help="Agent platform (k8s, ecs, or docker)",
)
@click.option(
    "--registry-url",
    help="Container registry URL for Docker images (e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo)",
)
@click.option(
    "--python-version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12", "3.13"]),
    help="Python version used to deploy the project",
)
@click.option(
    "--organization",
    help="Dagster Plus organization name",
)
@click.option(
    "--deployment",
    default="prod",
    help="Deployment name",
)
@click.option(
    "--git-root",
    type=Path,
    help="Path to the git repository root",
)
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts",
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def deploy_configure_hybrid(
    git_provider: Optional[str],
    agent_platform: Optional[str],
    registry_url: Optional[str],
    python_version: Optional[str],
    organization: Optional[str],
    deployment: Optional[str],
    git_root: Optional[Path],
    skip_confirmation_prompt: bool,
    use_editable_dagster: Optional[str],
    **global_options: object,
) -> None:
    """Scaffold deployment configuration for Dagster Plus Hybrid.

    This creates:
    - Dockerfile and build.yaml for containerization
    - container_context.yaml with platform-specific config (k8s/ecs/docker)
    - Required files for CI/CD based on your Git provider (GitHub Actions or GitLab CI)
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    resolved_platform = DgPlusAgentPlatform(agent_platform.upper()) if agent_platform else None
    resolved_git_provider = GitProvider(git_provider) if git_provider else None

    config = _resolve_config_with_prompts(
        agent_type=DgPlusAgentType.HYBRID,
        agent_platform=resolved_platform,
        organization=organization,
        deployment=deployment,
        git_root=git_root,
        python_version=python_version,
        skip_confirmation_prompt=skip_confirmation_prompt,
        use_editable_dagster=bool(use_editable_dagster),
        git_provider=resolved_git_provider,
        dg_context=dg_context,
        cli_config=cli_config,
        registry_url=registry_url,
    )

    configure_build_artifacts_impl(config)
    configure_ci_impl(config)


deploy_configure_group.add_command(deploy_configure_serverless)
deploy_configure_group.add_command(deploy_configure_hybrid)
