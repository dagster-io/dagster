from collections.abc import Mapping
from pathlib import Path

import click
from dagster_shared.plus.config import DagsterPlusCliConfig
from rich.console import Console
from rich.table import Table

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import ProjectEnvVars
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.plus.gql import LOCAL_SECRETS_FILE_QUERY
from dagster_dg.utils.plus.gql_client import DagsterCloudGraphQLClient
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="env", cls=DgClickGroup)
def env_group():
    """Commands for managing environment variables."""


# ########################
# ##### ENVIRONMENT
# ########################


@env_group.command(name="list", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def list_env_command(**global_options: object) -> None:
    """List environment variables from the .env file of the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    env = ProjectEnvVars.from_ctx(dg_context)
    if not env.values:
        click.echo("No environment variables are defined for this project.")
        return

    table = Table(border_style="dim")
    table.add_column("Env Var")
    table.add_column("Value")
    for key, value in env.values.items():
        table.add_row(key, value)
    console = Console()
    console.print(table)


# ########################
# ##### PULL
# ########################


def _get_local_secrets_for_locations(
    client: DagsterCloudGraphQLClient, location_names: set[str]
) -> Mapping[str, Mapping[str, str]]:
    secrets_by_location = {location_name: {} for location_name in location_names}

    result = client.execute(LOCAL_SECRETS_FILE_QUERY)
    for secret in result["secretsOrError"]["secrets"]:
        if not secret["localDeploymentScope"]:
            continue
        for location_name in location_names:
            if len(secret["locationNames"]) == 0 or location_name in secret["locationNames"]:
                secrets_by_location[location_name][secret["secretName"]] = secret["secretValue"]

    return secrets_by_location


@env_group.command(name="pull", cls=DgClickCommand)
@dg_global_options
def pull_env_command(**global_options: object) -> None:
    """Pull environment variables from the current project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)
    config = DagsterPlusCliConfig.get()

    project_ctxs = []
    if dg_context.is_workspace:
        project_ctxs = [
            dg_context.for_project_environment(project_spec.path, cli_config)
            for project_spec in dg_context.project_specs
        ]
    else:
        project_ctxs = [dg_context]

    gql_client = DagsterCloudGraphQLClient.from_config(config)
    secrets_by_location = _get_local_secrets_for_locations(
        gql_client, {project_ctx.project_name for project_ctx in project_ctxs}
    )

    for project_ctx in project_ctxs:
        env = ProjectEnvVars.empty(project_ctx).with_values(
            secrets_by_location[project_ctx.project_name]
        )
        env.write()

    if dg_context.is_project:
        click.echo("Environment variables saved to .env")
    else:
        click.echo("Environment variables saved to .env for all projects in the workspace")
