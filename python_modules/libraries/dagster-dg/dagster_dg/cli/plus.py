import itertools
import os
import webbrowser
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any

import click
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.login_server import start_login_server

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.env import ProjectEnvVars
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.plus import gql
from dagster_dg.utils.plus.gql_client import DagsterCloudGraphQLClient
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="plus", cls=DgClickGroup, hidden=True)
def plus_group():
    """Commands for interacting with Dagster Plus."""


@plus_group.command(name="login", cls=DgClickCommand)
@cli_telemetry_wrapper
def login_command() -> None:
    """Login to Dagster Plus."""
    org_url = DagsterPlusCliConfig.get().url if DagsterPlusCliConfig.exists() else None
    server, url = start_login_server(org_url)

    try:
        webbrowser.open(url, new=0, autoraise=True)
        click.echo(
            f"Opening browser...\nIf a window does not open automatically, visit {url} to"
            " finish authorization"
        )
    except webbrowser.Error as e:
        click.echo(f"Error launching web browser: {e}\n\nTo finish authorization, visit {url}\n")

    server.serve_forever()
    new_org = server.get_organization()
    new_api_token = server.get_token()

    config = DagsterPlusCliConfig(
        organization=new_org,
        user_token=new_api_token,
        url=org_url,
    )
    config.write()
    click.echo(f"Authorized for organization {new_org}\n")

    gql_client = DagsterCloudGraphQLClient.from_config(config)
    result = gql_client.execute(gql.FULL_DEPLOYMENTS_QUERY)
    deployment_names = [d["deploymentName"] for d in result["fullDeployments"]]

    click.echo("Available deployments: " + ", ".join(deployment_names))

    selected_deployment = None
    while selected_deployment not in deployment_names:
        if selected_deployment is not None:
            click.echo(f"{selected_deployment} is not a valid deployment")
        selected_deployment = click.prompt(
            "Select a default deployment", default=deployment_names[0]
        )

    config = DagsterPlusCliConfig(
        organization=config.organization,
        user_token=config.user_token,
        default_deployment=selected_deployment,
        url=org_url,
    )
    config.write()


# ########################
# ##### PLUS ENV MANAGEMENT
# ########################


@plus_group.group(name="env", cls=DgClickGroup)
def plus_env_group():
    """Commands for managing environment variables in Dagster Plus."""


def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus env pull` requires authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def _get_local_secrets_for_locations(
    client: DagsterCloudGraphQLClient, location_names: set[str]
) -> Mapping[str, Mapping[str, str]]:
    secrets_by_location = {location_name: {} for location_name in location_names}

    result = client.execute(gql.LOCAL_SECRETS_FILE_QUERY)
    for secret in result["viewableLocalSecretsOrError"]["secrets"]:
        if not secret["localDeploymentScope"]:
            continue
        for location_name in location_names:
            if len(secret["locationNames"]) == 0 or location_name in secret["locationNames"]:
                secrets_by_location[location_name][secret["secretName"]] = secret["secretValue"]

    return secrets_by_location


@plus_env_group.command(name="pull", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
def pull_env_command(**global_options: object) -> None:
    """Pull environment variables from Dagster Plus and save to a .env file for local use."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)
    config = _get_config_or_error()

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


class Scope(str, Enum):
    LOCAL = "local"
    BRANCH = "branch"
    FULL = "full"


def _secret_is_global(secret: Mapping[str, Any]) -> bool:
    return not secret["locationNames"]


def _get_secret_scopes(secret: Mapping[str, Any]) -> set[Scope]:
    return {
        s
        for s in {
            Scope.FULL if secret["fullDeploymentScope"] else None,
            Scope.BRANCH if secret["allBranchDeploymentsScope"] else None,
            Scope.LOCAL if secret["localDeploymentScope"] else None,
        }
        if s is not None
    }


@plus_env_group.command(name="add", cls=DgClickCommand)
@click.argument("env_name")
@click.argument("env_value", type=click.STRING, required=False)
@click.option(
    "--from-local-env",
    is_flag=True,
    help="Pull the environment variable value from your shell environment or project .env file.",
)
@click.option(
    "--scope",
    type=click.Choice(["full", "branch", "local"]),
    multiple=True,
    help="The deployment scope to set the environment variable in. Defaults to all scopes.",
)
@click.option(
    "--global",
    "global_",
    is_flag=True,
    help="Whether to set the environment variable at the deployment level, for all locations.",
)
@dg_global_options
@cli_telemetry_wrapper
def add_env_command(
    env_name: str,
    env_value: str,
    scope: list[str],
    global_: bool,
    from_local_env: bool,
    **global_options: object,
) -> None:
    """Set an environment variable in Dagster Plus."""
    if not env_value and not from_local_env:
        raise click.UsageError(
            "Environment variable value is required. You can either directly provide this value or use the --from-local-env flag to pull the value from your shell environment or project .env file."
        )
    if env_value and from_local_env:
        raise click.UsageError(
            "Environment variable value and --from-local-env cannot both be provided."
        )

    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    if from_local_env:
        local_env_value = ProjectEnvVars.from_ctx(dg_context).get(env_name)
        if local_env_value:
            click.echo(f"Reading environment variable {env_name} from project .env file")
        else:
            local_env_value = os.getenv(env_name)
            if local_env_value:
                click.echo(f"Reading environment variable {env_name} from shell environment")
            else:
                raise click.UsageError(
                    f"Environment variable {env_name} not found in your CLI environment or project .env file."
                )
        env_value = local_env_value

    config = _get_config_or_error()

    active_scopes = set(Scope(s) for s in scope) or {Scope.FULL, Scope.BRANCH, Scope.LOCAL}
    gql_client = DagsterCloudGraphQLClient.from_config(config)

    location_suffix = "" if global_ else f" for location {dg_context.project_name}"
    scope_text = f" in {', '.join(sorted(active_scopes))} scope"

    existing_secrets = gql_client.execute(
        gql.GET_SECRETS_FOR_SCOPES_QUERY,
        variables={
            "locationName": None if global_ else dg_context.project_name,
            "scopes": {
                "fullDeploymentScope": Scope.FULL in active_scopes,
                "allBranchDeploymentsScope": Scope.BRANCH in active_scopes,
                "localDeploymentScope": Scope.LOCAL in active_scopes,
            },
            "secretName": env_name,
        },
    )["secretsForScopes"]["secrets"]

    for existing_secret in existing_secrets:
        if len(existing_secret["locationNames"]) > 1:
            raise click.ClickException(
                f"Environment variable {env_name} is configured for multiple locations {', '.join(existing_secret['locationNames'])}, and cannot be modified via the CLI."
            )

    should_confirm = False
    any_secret_is_global = any(
        _secret_is_global(existing_secret) for existing_secret in existing_secrets
    )
    if not global_ and any_secret_is_global:
        click.echo(
            f"Environment variable {env_name} is set globally within the current deployment. The current command will only update the value for location {dg_context.project_name}. Use --global to update this value for all locations."
        )
        should_confirm = True

    existing_scopes = set(
        itertools.chain.from_iterable(
            _get_secret_scopes(existing_secret)
            for existing_secret in existing_secrets
            if global_ or existing_secret["locationNames"]
        )
    )
    if existing_scopes:
        click.echo(
            f"Environment variable {env_name} is already configured for {', '.join(s.value for s in existing_scopes)} scope{location_suffix}."
        )
        should_confirm = True

    if should_confirm:
        if not global_:
            click.confirm(
                f"\nAre you sure you want to update environment variable {env_name}{scope_text}{location_suffix}?",
                abort=True,
            )
        else:
            click.confirm(
                f"\nAre you sure you want to update environment variable {env_name}{scope_text} for all locations?",
                abort=True,
            )

    gql_client.execute(
        gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
        variables={
            "secretName": env_name,
            "secretValue": env_value,
            "scopes": {
                "fullDeploymentScope": Scope.FULL in active_scopes,
                "allBranchDeploymentsScope": Scope.BRANCH in active_scopes,
                "localDeploymentScope": Scope.LOCAL in active_scopes,
            },
            "locationName": None if global_ else dg_context.project_name,
        },
    )

    if global_:
        click.echo(
            f"\nEnvironment variable {env_name} set{scope_text} for all locations in deployment {config.default_deployment}"
        )
    else:
        click.echo(
            f"\nEnvironment variable {env_name} set{scope_text}{location_suffix} in deployment {config.default_deployment}"
        )
