from typing import Optional

import typer
from typer import Typer

from dagster_cloud_cli import gql, ui
from dagster_cloud_cli.config_utils import dagster_cloud_options

app = Typer(help="Commands for working with Dagster Cloud runs.")


@app.command(name="status")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def status(
    api_token: str,
    url: str,
    deployment: Optional[str],
    run_id: str = typer.Argument(None),
):
    """Check the status of a run."""
    # this should be replaced by using the `dagster` CLI against a dagster-cloud `dagster.yaml`
    if not run_id:
        raise ui.error("No run_id provided")

    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        try:
            ui.print(gql.run_status(client, run_id))
        except Exception as e:
            ui.error(f"Failed to get status for run {run_id}: {e}.")
