"""Legacy command for scaffolding build artifacts.

This command is maintained for backward compatibility.
Consider using `dg plus deploy configure [serverless|hybrid]` instead.
"""

from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_editable_dagster_options, dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.cli.plus.deploy.configure.commands import resolve_python_version
from dagster_dg_cli.cli.plus.deploy.configure.configure_build_artifacts import (
    configure_build_artifacts_impl,
)
from dagster_dg_cli.cli.plus.deploy.configure.utils import DgPlusDeployConfigureOptions
from dagster_dg_cli.utils.plus.build import get_agent_type_and_platform_from_graphql
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


def _resolve_config_for_build_artifacts(
    python_version: Optional[str],
    skip_confirmation_prompt: bool,
    use_editable_dagster: bool,
    dg_context: DgContext,
    cli_config,
) -> DgPlusDeployConfigureOptions:
    """Resolve config for legacy build-artifacts command.

    This command only scaffolds build artifacts (no CI/CD), and tries to detect
    agent type/platform from Plus config but doesn't prompt if unavailable.
    """
    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    # Try to detect agent type and platform from Plus config
    agent_type = None
    agent_platform = None
    if plus_config:
        try:
            gql_client = DagsterPlusGraphQLClient.from_config(plus_config)
            agent_type, agent_platform = get_agent_type_and_platform_from_graphql(gql_client)
        except Exception:
            # If GraphQL fails, just proceed without it
            pass

    # Default to HYBRID if we couldn't detect it
    if agent_type is None:
        agent_type = DgPlusAgentType.HYBRID

    resolved_python_version = resolve_python_version(python_version)

    return DgPlusDeployConfigureOptions(
        dg_context=dg_context,
        cli_config=cli_config,
        plus_config=plus_config,
        agent_type=agent_type,
        agent_platform=agent_platform,
        organization_name=None,
        deployment_name="prod",
        git_root=None,
        python_version=resolved_python_version,
        skip_confirmation_prompt=skip_confirmation_prompt,
        git_provider=None,
        use_editable_dagster=use_editable_dagster,
    )


@click.command(name="build-artifacts", cls=DgClickCommand)
@click.option(
    "--python-version",
    "python_version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12", "3.13"]),
    help=(
        "Python version used to deploy the project. If not set, defaults to the calling process's Python minor version."
    ),
)
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts.",
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_build_artifacts_command(
    python_version: Optional[str],
    use_editable_dagster: Optional[str],
    skip_confirmation_prompt: bool,
    **global_options: object,
) -> None:
    """Scaffolds a Dockerfile to build the given Dagster project or workspace.

    NOTE: This command is maintained for backward compatibility.
    Consider using `dg plus deploy configure [serverless|hybrid]` instead for a complete
    deployment setup including CI/CD configuration.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    config = _resolve_config_for_build_artifacts(
        python_version=python_version,
        skip_confirmation_prompt=skip_confirmation_prompt,
        use_editable_dagster=bool(use_editable_dagster),
        dg_context=dg_context,
        cli_config=cli_config,
    )

    configure_build_artifacts_impl(config)
