import itertools
import os
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.env import ProjectEnvVars
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus import gql
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


class EnvVarScope(str, Enum):
    """Env var scopes in Dagster Plus.

    local corresponds to secrets pulled with `dg plus env pull`,
    branch corresponds to secrets set in branch deployments,
    full corresponds to secrets set in full deployments.
    """

    LOCAL = "local"
    BRANCH = "branch"
    FULL = "full"


def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def _secret_is_global(secret: Mapping[str, Any]) -> bool:
    return not secret["locationNames"]


def _get_secret_scopes(secret: Mapping[str, Any]) -> set[EnvVarScope]:
    return {
        s
        for s in {
            EnvVarScope.FULL if secret["fullDeploymentScope"] else None,
            EnvVarScope.BRANCH if secret["allBranchDeploymentsScope"] else None,
            EnvVarScope.LOCAL if secret["localDeploymentScope"] else None,
        }
        if s is not None
    }


@click.command(name="env", cls=DgClickCommand)
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
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Do not confirm the creation of the environment variable, if it already exists.",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def create_env_command(
    env_name: str,
    env_value: str,
    scope: list[str],
    global_: bool,
    from_local_env: bool,
    skip_confirmation_prompt: bool,
    target_path: Path,
    **global_options: object,
) -> None:
    """Create or update an environment variable in Dagster Plus."""
    if not env_value and not from_local_env:
        raise click.UsageError(
            "Environment variable value is required. You can either directly provide this value or use the --from-local-env flag to pull the value from your shell environment or project .env file."
        )
    if env_value and from_local_env:
        raise click.UsageError(
            "Environment variable value and --from-local-env cannot both be provided."
        )

    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)
    if not dg_context.is_project:
        global_ = True

    if from_local_env:
        local_env_value = (
            ProjectEnvVars.from_ctx(dg_context).get(env_name) if dg_context.is_project else None
        )
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

    active_scopes = set(EnvVarScope(s) for s in scope) or {
        EnvVarScope.FULL,
        EnvVarScope.BRANCH,
        EnvVarScope.LOCAL,
    }
    gql_client = DagsterPlusGraphQLClient.from_config(config)

    location_suffix = "" if global_ else f" for location {dg_context.project_name}"
    scope_text = f" in {', '.join(sorted(active_scopes))} scope"

    existing_secrets = gql_client.execute(
        gql.GET_SECRETS_FOR_SCOPES_QUERY,
        variables={
            "locationName": None if global_ else dg_context.project_name,
            "scopes": {
                "fullDeploymentScope": EnvVarScope.FULL in active_scopes,
                "allBranchDeploymentsScope": EnvVarScope.BRANCH in active_scopes,
                "localDeploymentScope": EnvVarScope.LOCAL in active_scopes,
            },
            "secretName": env_name,
        },
    )["secretsOrError"]["secrets"]
    if global_:
        existing_secrets = [
            secret for secret in existing_secrets if len(secret["locationNames"]) == 0
        ]

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

    if should_confirm and not skip_confirmation_prompt:
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
                "fullDeploymentScope": EnvVarScope.FULL in active_scopes,
                "allBranchDeploymentsScope": EnvVarScope.BRANCH in active_scopes,
                "localDeploymentScope": EnvVarScope.LOCAL in active_scopes,
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
