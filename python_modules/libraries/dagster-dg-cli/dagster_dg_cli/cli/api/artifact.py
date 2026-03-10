"""Artifact upload/download commands using REST endpoints with presigned S3 URLs."""

from pathlib import Path

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.api_layer.api.artifact import DgApiArtifactApi
from dagster_dg_cli.cli.api.formatters import format_artifact_download, format_artifact_upload
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="upload", cls=DgClickCommand)
@click.argument("key")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--deployment",
    help="Deployment name for deployment-scoped artifacts. If omitted, artifact is organization-scoped.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.artifact", cls="ArtifactUploadResult")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def upload_artifact_command(
    ctx: click.Context,
    key: str,
    path: str,
    deployment: str | None,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Upload an artifact to Dagster Plus.

    KEY is the artifact key (e.g. "my-model/latest").
    PATH is the local file path to upload.
    """
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )

    api = DgApiArtifactApi(
        base_url=config.organization_url,
        headers={
            "Dagster-Cloud-Api-Token": api_token,
            "Dagster-Cloud-Organization": organization,
        },
    )

    with handle_api_errors(ctx, output_json):
        result = api.upload(key=key, path=Path(path), deployment=deployment)
        click.echo(format_artifact_upload(result, as_json=output_json))


@click.command(name="download", cls=DgClickCommand)
@click.argument("key")
@click.argument("path", type=click.Path())
@click.option(
    "--deployment",
    help="Deployment name for deployment-scoped artifacts. If omitted, artifact is organization-scoped.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.artifact", cls="ArtifactDownloadResult"
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def download_artifact_command(
    ctx: click.Context,
    key: str,
    path: str,
    deployment: str | None,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Download an artifact from Dagster Plus.

    KEY is the artifact key (e.g. "my-model/latest").
    PATH is the local file path to save to.
    """
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )

    api = DgApiArtifactApi(
        base_url=config.organization_url,
        headers={
            "Dagster-Cloud-Api-Token": api_token,
            "Dagster-Cloud-Organization": organization,
        },
    )

    with handle_api_errors(ctx, output_json):
        result = api.download(key=key, path=Path(path), deployment=deployment)
        click.echo(format_artifact_download(result, as_json=output_json))


@click.group(
    name="artifact",
    cls=DgClickGroup,
    commands={
        "upload": upload_artifact_command,
        "download": download_artifact_command,
    },
)
def artifact_group():
    """Upload and download artifacts in Dagster Plus."""
