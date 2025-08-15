from typing import Optional

import click
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus import gql
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


@click.command(name="ci-api-token", cls=DgClickCommand)
@click.option("--description", type=str, help="Description for the token")
@dg_global_options
@cli_telemetry_wrapper
def create_ci_api_token(description: Optional[str] = None, **global_options: object) -> None:
    """Create a Dagster Plus API token for CI."""
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus create ci-api-token` requires authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    config = DagsterPlusCliConfig.get()

    gql_client = DagsterPlusGraphQLClient.from_config(config)

    token_data = gql_client.execute(
        gql.CREATE_AGENT_TOKEN_MUTATION, variables={"description": description}
    )
    click.echo(token_data["createAgentToken"]["token"])
