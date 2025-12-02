"""Legacy command for scaffolding GitHub Actions workflow.

This command is maintained for backward compatibility.
Consider using `dg plus deploy configure [serverless|hybrid] --git-provider github` instead.
"""

from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.cli.plus.deploy.configure.commands import (
    resolve_deployment,
    resolve_git_root,
    resolve_organization,
    resolve_python_version,
)
from dagster_dg_cli.cli.plus.deploy.configure.configure_ci import configure_ci_impl
from dagster_dg_cli.cli.plus.deploy.configure.utils import DgPlusDeployConfigureOptions, GitProvider
from dagster_dg_cli.utils.plus.build import get_agent_type_and_platform_from_graphql
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


def _resolve_config_for_github_actions(
    git_root: Optional[Path],
    dg_context: DgContext,
    cli_config,
) -> DgPlusDeployConfigureOptions:
    """Resolve config for legacy github-actions command.

    This command prompts in the legacy order: org, deployment, agent type (no platform).
    """
    from dagster_shared.plus.config import DagsterPlusCliConfig

    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    # Prompt for org and deployment FIRST (legacy order)
    resolved_organization = resolve_organization(None, plus_config)
    resolved_deployment = resolve_deployment(None, plus_config)

    # Try to detect agent type and platform from Plus config
    agent_type = None
    agent_platform = None
    if plus_config:
        try:
            gql_client = DagsterPlusGraphQLClient.from_config(plus_config)
            agent_type, agent_platform = get_agent_type_and_platform_from_graphql(gql_client)
        except Exception:
            pass

    # Prompt for agent type if not detected
    if agent_type is None:
        agent_type = DgPlusAgentType(
            click.prompt(
                "Deployment agent type",
                type=click.Choice(["serverless", "hybrid"]),
            ).upper()
        )

    # Resolve git root
    resolved_git_root = resolve_git_root(git_root, GitProvider.GITHUB)

    # Use default Python version
    resolved_python_version = resolve_python_version(None)

    return DgPlusDeployConfigureOptions(
        dg_context=dg_context,
        cli_config=cli_config,
        plus_config=plus_config,
        agent_type=agent_type,
        agent_platform=agent_platform,  # May be None - legacy didn't require platform
        organization_name=resolved_organization,
        deployment_name=resolved_deployment,
        git_root=resolved_git_root,
        python_version=resolved_python_version,
        skip_confirmation_prompt=False,
        git_provider=GitProvider.GITHUB,
        use_editable_dagster=False,
    )


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

    NOTE: This command is maintained for backward compatibility.
    Consider using `dg plus deploy configure [serverless|hybrid] --git-provider github`
    instead for a complete deployment setup.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    config = _resolve_config_for_github_actions(
        git_root=git_root,
        dg_context=dg_context,
        cli_config=cli_config,
    )

    configure_ci_impl(config)
