"""Validation for dg plus deploy commands."""

import pathlib
from typing import Optional

import click
from dagster_shared.plus.config import DagsterPlusCliConfig


def _extract_dagster_env_from_url(url: Optional[str]) -> Optional[str]:
    """Extract dagster_env from a DagsterPlusCliConfig URL.

    Args:
        url: Base URL like "https://eu.dagster.cloud" or None

    Returns:
        "eu" if EU region, None otherwise
    """
    if url and "eu.dagster.cloud" in url:
        return "eu"
    return None


def validate_deploy_configuration(
    dagster_cloud_yaml_path: str,
    organization: str,
) -> None:
    """Validate deployment configuration before starting deploy session.

    Performs:
    - YAML schema validation (structure, required fields, build directories)
    - API connectivity check (token + GraphQL query)

    Args:
        dagster_cloud_yaml_path: Path to the dagster_cloud.yaml file to validate
        organization: Dagster Cloud organization name

    Raises:
        click.ClickException: If validation fails
    """
    # defer for import performance
    from dagster_cloud_cli.commands.ci import checks
    from dagster_cloud_cli.config_utils import get_org_url

    yaml_path = pathlib.Path(dagster_cloud_yaml_path)

    yaml_result = checks.check_dagster_cloud_yaml(yaml_path)

    dagster_env = None
    if DagsterPlusCliConfig.exists():
        config = DagsterPlusCliConfig.get()
        dagster_env = _extract_dagster_env_from_url(config.url)

    url = get_org_url(organization, dagster_env)
    connect_result = checks.check_connect_dagster_cloud(url)

    all_errors = yaml_result.errors + connect_result.errors

    if all_errors:
        click.echo(click.style("\nConfiguration validation failed:", fg="red", bold=True))
        click.echo()
        for error in all_errors:
            click.echo(f"  • {error}")
        click.echo()
        click.echo(
            click.style("Fix the errors above or use --skip-validation to bypass.", dim=True)
        )
        raise click.ClickException("Deploy configuration validation failed")

    click.echo("Configuration validated")
