from pathlib import Path
from typing import Optional

import yaml
from typer import Option, Typer

from .... import gql, ui
from ....config_utils import dagster_cloud_options

DEFAULT_ALERT_POLICIES_YAML_FILENAME = "alert_policies.yaml"

app = Typer(help="Interact with your alert policies.")


@app.command(name="list")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def list_command(
    api_token: str,
    url: str,
    deployment: Optional[str],
):
    """List your alert policies, output in YAML format."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        alert_policies_response = gql.get_alert_policies(client)

    ui.print_yaml(alert_policies_response)


@app.command(name="sync")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def sync_command(
    api_token: str,
    url: str,
    deployment: Optional[str],
    alert_policies_file: Path = Option(
        DEFAULT_ALERT_POLICIES_YAML_FILENAME,
        "--alert-policies",
        "-a",
        exists=True,
        help="Path to alert policies file.",
    ),
):
    """Sync your YAML configured alert policies to Dagster Cloud."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        with open(str(alert_policies_file), encoding="utf8") as f:
            config = yaml.load(f.read(), Loader=yaml.SafeLoader)

        try:
            alert_policies = gql.reconcile_alert_policies(client, config)

            ui.print(f"Synced alert policies: {', '.join(alert_policies)}")
        except Exception as e:
            raise ui.error(str(e))
