import json
import os
from typing import Any, Optional
from uuid import uuid4

import typer
from typer import Typer

from dagster_cloud_cli import gql, ui
from dagster_cloud_cli.config_utils import dagster_cloud_options

app = Typer(help="Commands for working with Dagster Cloud jobs.")


SINGLETON_REPOSITORY_NAME = "__repository__"


@app.command(name="launch")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def launch(
    api_token: str,
    url: str,
    deployment: Optional[str],
    location: str = typer.Option(..., "-l", "--location", help="Location name in the deployment."),
    job: str = typer.Option(..., "-j", "--job", help="Job name to run."),
    repository: str = typer.Option(
        None,
        "-r",
        "--repository",
        help=(
            "Repository in the specified code location. Required if a repository is defined in the"
            " specified code location."
        ),
    ),
    tags: str = typer.Option(None, "--tags", help="JSON dict of tags to use for this job run."),
    config: str = typer.Option(
        None, "--config-json", help="JSON string of run config to use for this job run"
    ),
    asset_keys: Optional[list[str]] = typer.Option(
        None,
        "--asset-key",
        help=(
            "Asset key to materialize. Can be specified multiple times to materialize multiple"
            " assets."
        ),
    ),
):
    """Launch a run for a job."""
    loaded_tags: dict[str, Any] = json.loads(tags) if tags else {}
    loaded_config: dict[str, Any] = json.loads(config) if config else {}

    repository = repository or SINGLETON_REPOSITORY_NAME

    headers: dict[str, str] = {
        "Idempotency-Key": str(uuid4()),
    }

    with gql.graphql_client_from_url(
        url,
        api_token,
        deployment_name=deployment,
        headers=headers,
        retries=int(os.getenv("DAGSTER_CLOUD_JOB_LAUNCH_RETRIES", "5")),
    ) as client:
        ui.print(
            gql.launch_run(
                client,
                location,
                repository,
                job,
                loaded_tags,
                loaded_config,
                asset_keys=asset_keys,
            )
        )
