"""Alert policy API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_alert_policies, format_alert_policy_sync_result
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.alert_policy", cls="AlertPolicyDocument"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_alert_policies_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List alert policies for a deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.alert_policies import DgApiAlertPolicyApi

    api = DgApiAlertPolicyApi(client)

    with handle_api_errors(ctx, output_json):
        policies = api.list_alert_policies()
        output = format_alert_policies(policies, as_json=output_json)
        click.echo(output)


@click.command(name="sync", cls=DgClickCommand)
@click.argument("file_path", required=True, type=click.Path(exists=True))
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.alert_policy", cls="AlertPolicySyncResult"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def sync_alert_policies_command(
    ctx: click.Context,
    file_path: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Sync alert policies from a YAML file."""
    import yaml

    with open(file_path) as f:
        config = yaml.safe_load(f)

    if not isinstance(config, (list, dict)):
        raise click.ClickException(
            f"Expected a YAML list or mapping in {file_path}, got {type(config).__name__}"
        )

    # Support both raw list and dict with "alert_policies" key
    if isinstance(config, dict):
        alert_policies = config.get("alert_policies", [])
    else:
        alert_policies = config

    cli_config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, cli_config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.alert_policies import DgApiAlertPolicyApi

    api = DgApiAlertPolicyApi(client)

    with handle_api_errors(ctx, output_json):
        result = api.sync_alert_policies(alert_policies)
        output = format_alert_policy_sync_result(result, as_json=output_json)
        click.echo(output)


@click.group(
    name="alert-policy",
    cls=DgClickGroup,
    commands={
        "list": list_alert_policies_command,
        "sync": sync_alert_policies_command,
    },
)
def alert_policy_group():
    """Manage alert policies in Dagster Plus."""
