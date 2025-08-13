from collections.abc import Mapping
from pathlib import Path

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.env import ProjectEnvVars
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql import SECRETS_QUERY
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def _get_local_secrets_for_locations(
    client: DagsterPlusGraphQLClient, location_names: set[str]
) -> Mapping[str, Mapping[str, str]]:
    secrets_by_location = {location_name: {} for location_name in location_names}

    result = client.execute(
        SECRETS_QUERY,
        variables={"onlyViewable": True, "scopes": {"localDeploymentScope": True}},
    )
    for secret in result["secretsOrError"]["secrets"]:
        if not secret["localDeploymentScope"]:
            continue
        for location_name in location_names:
            if len(secret["locationNames"]) == 0 or location_name in secret["locationNames"]:
                secrets_by_location[location_name][secret["secretName"]] = secret["secretValue"]

    return secrets_by_location


@click.command(name="env", cls=DgClickCommand)
@dg_global_options
@dg_path_options
@cli_telemetry_wrapper
def pull_env_command(target_path: Path, **global_options: object) -> None:
    """Pull environment variables from Dagster Plus and save to a .env file for local use."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)
    config = _get_config_or_error()

    project_ctxs = []

    if dg_context.is_project:
        project_ctxs = [dg_context]
    else:
        project_ctxs = [
            dg_context.for_project_environment(project_spec.path, cli_config)
            for project_spec in dg_context.project_specs
        ]

    gql_client = DagsterPlusGraphQLClient.from_config(config)
    secrets_by_location = _get_local_secrets_for_locations(
        gql_client, {project_ctx.project_name for project_ctx in project_ctxs}
    )

    projects_without_secrets = {project_ctx.project_name for project_ctx in project_ctxs}
    for project_ctx in project_ctxs:
        if secrets_by_location[project_ctx.project_name]:
            env = ProjectEnvVars.empty(project_ctx).with_values(
                secrets_by_location[project_ctx.project_name]
            )
            env.write()
            projects_without_secrets.remove(project_ctx.project_name)

    if dg_context.is_project:
        click.echo("Environment variables saved to .env")
    else:
        click.echo("Environment variables saved to .env for projects in workspace")
        if projects_without_secrets:
            click.echo(
                f"Environment variables not found for projects: {', '.join(projects_without_secrets)}"
            )
