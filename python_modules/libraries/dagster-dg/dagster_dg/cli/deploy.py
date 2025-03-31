from pathlib import Path

import click
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import ProjectEnvVars, get_project_specified_env_vars
from dagster_dg.utils import DgClickCommand
from dagster_dg.utils.plus import gql
from dagster_dg.utils.plus.gql_client import DagsterCloudGraphQLClient
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

# ########################
# ##### ENVIRONMENT
# ########################


@click.command(name="deploy", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def deploy_command(**global_options: object) -> None:
    """Deploy a Dagster project."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    env_vars = get_project_specified_env_vars(dg_context)

    env = ProjectEnvVars.from_ctx(dg_context)

    env_var_keys = set(env.values.keys()) | set(env_vars.keys())

    if DagsterPlusCliConfig.exists():
        scopes_for_key = {}
        config = DagsterPlusCliConfig.get()
        gql_client = DagsterCloudGraphQLClient.from_config(config)
        for key in env_var_keys:
            secrets_by_location = gql_client.execute(
                gql.GET_SECRETS_FOR_SCOPES_QUERY,
                {
                    "locationName": dg_context.project_name,
                    "scopes": {
                        "fullDeploymentScope": True,
                        "allBranchDeploymentsScope": True,
                        "localDeploymentScope": True,
                    },
                    "secretName": key,
                },
            )["secretsForScopes"]["secrets"]
            scopes_for_key[key] = {
                "full": any(secret["fullDeploymentScope"] for secret in secrets_by_location),
                "branch": any(
                    secret["allBranchDeploymentsScope"] for secret in secrets_by_location
                ),
                "local": any(secret["localDeploymentScope"] for secret in secrets_by_location),
            }

    if not all(scopes_for_key[key]["full"] for key in env_var_keys):
        click.echo(
            f"Missing environment variables for deployment {config.default_deployment} in full deployment scope, for location {dg_context.project_name}:"
        )
        for key in env_var_keys:
            if not scopes_for_key[key]["full"]:
                click.echo(f"  {key}")
        import sys

        sys.exit(1)
