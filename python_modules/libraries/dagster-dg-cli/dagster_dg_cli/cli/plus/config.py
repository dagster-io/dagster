import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import (
    DEPLOYMENT_ENV_VAR_NAME,
    ORGANIZATION_ENV_VAR_NAME,
    TOKEN_ENV_VAR_NAME,
)

EU_DAGSTER_CLOUD_URL = "https://eu.dagster.cloud"


@click.group(
    name="config",
    cls=DgClickGroup,
    commands={"set": "config_set_command"},
)
def config_group():
    """Manage Dagster Plus CLI configuration."""


@click.command(name="set", cls=DgClickCommand)
@click.option(
    "--api-token",
    envvar=TOKEN_ENV_VAR_NAME,
    default=None,
    help="API token for authentication (or set DAGSTER_CLOUD_API_TOKEN).",
)
@click.option(
    "--organization",
    "-o",
    envvar=ORGANIZATION_ENV_VAR_NAME,
    default=None,
    help="Organization name (or set DAGSTER_CLOUD_ORGANIZATION).",
)
@click.option(
    "--deployment",
    "-d",
    envvar=DEPLOYMENT_ENV_VAR_NAME,
    default=None,
    help="Default deployment (or set DAGSTER_CLOUD_DEPLOYMENT).",
)
@click.option(
    "--url",
    default=None,
    help="Direct URL override for the Dagster Plus instance.",
)
@click.option(
    "--region",
    type=click.Choice(["us", "eu"]),
    default=None,
    help="Dagster Cloud region. 'eu' sets URL to https://eu.dagster.cloud.",
)
@cli_telemetry_wrapper
def config_set_command(
    api_token: str | None,
    organization: str | None,
    deployment: str | None,
    url: str | None,
    region: str | None,
) -> None:
    """Set Dagster Plus CLI configuration values."""
    if region == "eu":
        resolved_url = EU_DAGSTER_CLOUD_URL
    elif url is not None:
        resolved_url = url
    else:
        resolved_url = None

    if not DagsterPlusCliConfig.exists() and not organization and not api_token:
        raise click.UsageError(
            "No existing configuration found. At minimum, --organization and --api-token "
            "are required when setting up configuration for the first time."
        )

    config = DagsterPlusCliConfig(
        organization=organization,
        user_token=api_token,
        default_deployment=deployment,
        url=resolved_url,
    )
    config.write()

    updated = []
    if organization:
        updated.append(f"organization: {organization}")
    if api_token:
        updated.append("api-token: ****")
    if deployment:
        updated.append(f"deployment: {deployment}")
    if resolved_url:
        updated.append(f"url: {resolved_url}")

    if updated:
        click.echo("Updated configuration:")
        for item in updated:
            click.echo(f"  {item}")
    else:
        click.echo("No configuration values were changed.")


# Wire up the group's commands dict
config_group.commands["set"] = config_set_command
