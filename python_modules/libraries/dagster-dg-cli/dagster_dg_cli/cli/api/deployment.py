"""Deployment API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import (
    format_deployment,
    format_deployment_settings,
    format_deployments,
)
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@click.option(
    "--type",
    "deployment_type",
    type=click.Choice(["production", "branch", "all"], case_sensitive=False),
    default="production",
    help="Type of deployments to list (default: production)",
)
@click.option(
    "--pr-status",
    "pr_status",
    type=click.Choice(["OPEN", "CLOSED", "MERGED"], case_sensitive=True),
    default=None,
    help="Filter branch deployments by pull request status (only applies with --type branch or all)",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.deployment", cls="DeploymentList")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_deployments_command(
    ctx: click.Context,
    output_json: bool,
    deployment_type: str,
    pr_status: str | None,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List deployments in the organization."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentList

    api = DgApiDeploymentApi(client)

    with handle_api_errors(ctx, output_json):
        if deployment_type == "production":
            deployments = api.list_deployments()
        elif deployment_type == "branch":
            deployments = api.list_branch_deployments(pull_request_status=pr_status)
        else:  # all
            prod = api.list_deployments()
            branch = api.list_branch_deployments(pull_request_status=pr_status)
            all_items = prod.items + branch.items
            deployments = DeploymentList(items=all_items, total=len(all_items))

        output = format_deployments(deployments, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("name", required=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.deployment", cls="Deployment")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_deployment_command(
    ctx: click.Context,
    name: str,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Show detailed information about a specific deployment."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    with handle_api_errors(ctx, output_json):
        try:
            deployment = api.get_deployment(name)
        except ValueError as e:
            if "Deployment not found" in str(e):
                raise click.ClickException(f"Deployment '{name}' not found")
            else:
                raise
        output = format_deployment(deployment, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.deployment", cls="DeploymentSettings")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_settings_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get settings for a deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    with handle_api_errors(ctx, output_json):
        settings = api.get_deployment_settings()
        output = format_deployment_settings(settings, as_json=output_json)
        click.echo(output)


@click.command(name="set", cls=DgClickCommand)
@click.argument("file_path", required=True, type=click.Path(exists=True))
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.deployment", cls="DeploymentSettings")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def set_settings_command(
    ctx: click.Context,
    file_path: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Set deployment settings from a YAML file."""
    import yaml

    with open(file_path) as f:
        settings_dict = yaml.safe_load(f)

    if not isinstance(settings_dict, dict):
        raise click.ClickException(
            f"Expected a YAML mapping in {file_path}, got {type(settings_dict).__name__}"
        )

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    with handle_api_errors(ctx, output_json):
        from dagster_dg_cli.api_layer.schemas.deployment import DeploymentSettings

        settings = api.update_deployment_settings(DeploymentSettings(settings=settings_dict))
        output = format_deployment_settings(settings, as_json=output_json)
        click.echo(output)


@click.group(
    name="settings",
    cls=DgClickGroup,
    commands={
        "get": get_settings_command,
        "set": set_settings_command,
    },
)
def settings_group():
    """Manage deployment settings."""


@click.group(
    name="deployment",
    cls=DgClickGroup,
    commands={
        "list": list_deployments_command,
        "get": get_deployment_command,
        "settings": settings_group,
    },
)
def deployment_group():
    """Manage deployments in Dagster Plus."""
