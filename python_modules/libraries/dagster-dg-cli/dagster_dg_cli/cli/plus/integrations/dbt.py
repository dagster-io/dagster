import os
from pathlib import Path
from typing import TYPE_CHECKING

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config_utils import dg_api_options

if TYPE_CHECKING:
    from dagster_dbt import DbtProject


@click.group(
    name="dbt",
    cls=DgClickGroup,
)
def dbt_group():
    """Commands for managing dbt integrations with Dagster Plus."""


def _discover_dbt_projects(
    components_path: Path | None, file_path: Path | None
) -> list["DbtProject"]:
    """Discover DbtProject instances from a components directory or Python file."""
    try:
        from dagster_dbt import DbtProject
    except ImportError:
        raise click.ClickException("Unable to import dagster_dbt. dagster-dbt must be installed.")

    if not components_path and not file_path:
        raise click.UsageError("Must specify --components or --file.")

    if file_path:
        from dagster._core.code_pointer import load_python_file
        from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types

        contents = load_python_file(file_path, None)
        return list(find_objects_in_module_of_types(contents, DbtProject))
    else:
        from dagster_dbt.components.dbt_project.component import get_projects_from_dbt_component

        assert components_path is not None  # guaranteed by earlier check
        return list(get_projects_from_dbt_component(components_path))


@dbt_group.command(name="manage-manifest", cls=DgClickCommand)
@click.option(
    "--components",
    "components_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to a dg project directory containing DbtProjectComponents.",
)
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to a Python file with DbtProject definitions.",
)
@click.option(
    "--source-deployment",
    default="prod",
    help="Which deployment should upload its manifest.json.",
)
@click.option(
    "--key-prefix",
    default="",
    help="A key prefix for the key the manifest.json is saved with.",
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
def manage_manifest_command(
    components_path: Path | None,
    file_path: Path | None,
    source_deployment: str,
    key_prefix: str,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Auto-manage dbt manifest upload/download based on deployment context.

    In branch deployments, downloads the prod manifest. In the source deployment
    (default: "prod"), uploads the manifest. Replaces `dagster-cloud ci project manage-state`.
    """
    from dagster_cloud_cli.commands.ci import state
    from dagster_cloud_cli.core.artifacts import (
        download_organization_artifact,
        upload_organization_artifact,
    )

    projects = _discover_dbt_projects(components_path, file_path)

    # Resolve deployment context from CI state
    from dagster_shared.seven.temp_dir import get_system_temp_directory

    statedir = os.getenv(
        "DAGSTER_BUILD_STATEDIR",
        str(Path(get_system_temp_directory()) / "dg-build-state"),
    )
    state_store = state.FileStore(statedir=statedir)
    locations = state_store.list_locations()
    if not locations:
        raise click.ClickException(
            "Unable to determine deployment state. "
            "Ensure a deploy session has been started (e.g. via `dg plus deploy start`)."
        )

    location = locations[0]
    deployment_name = location.deployment_name
    is_branch = location.is_branch_deployment

    for project in projects:
        if not project.state_path:
            continue

        download_path = project.state_path.joinpath("manifest.json")
        key = f"{key_prefix}{os.fspath(download_path)}"

        if is_branch:
            click.echo(f"Downloading {source_deployment} manifest for branch deployment.")
            project.state_path.mkdir(parents=True, exist_ok=True)
            download_organization_artifact(
                key=key,
                path=download_path,
                organization=organization,
                api_token=api_token,
            )
            click.echo("Download complete.")

        elif deployment_name == source_deployment:
            click.echo(f"Uploading {source_deployment} manifest.")
            upload_organization_artifact(
                key=key,
                path=project.manifest_path,
                organization=organization,
                api_token=api_token,
            )
            click.echo("Upload complete.")

        else:
            click.echo(
                f"Warning: Deployment named {deployment_name} does not match source "
                f"deployment {source_deployment}, taking no action. If this is the "
                f"desired dbt state artifacts to upload, set the cli flag "
                f"`--source-deployment {deployment_name}`."
            )


@dbt_group.command(name="download-manifest", cls=DgClickCommand)
@click.option(
    "--components",
    "components_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to a dg project directory containing DbtProjectComponents.",
)
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to a Python file with DbtProject definitions.",
)
@click.option(
    "--key-prefix",
    default="",
    help="A key prefix for the key the manifest.json is saved with.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Override the download destination path. Cannot be used with multiple projects.",
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
def download_manifest_command(
    components_path: Path | None,
    file_path: Path | None,
    key_prefix: str,
    output_path: Path | None,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Download a dbt manifest from Dagster Plus for local development.

    Downloads the manifest artifact stored at organization scope. Use --components
    to discover DbtProject instances from a dg project, or --file to point at a
    Python file containing DbtProject definitions.
    """
    from dagster_cloud_cli.core.artifacts import download_organization_artifact

    projects = _discover_dbt_projects(components_path, file_path)

    projects_with_state = [p for p in projects if p.state_path]
    if not projects_with_state:
        raise click.ClickException("No DbtProject instances with a state_path were found.")

    if output_path and len(projects_with_state) > 1:
        raise click.UsageError(
            "--output cannot be used when multiple DbtProject instances are found."
        )

    for project in projects_with_state:
        assert project.state_path is not None
        download_path = project.state_path.joinpath("manifest.json")
        key = f"{key_prefix}{os.fspath(download_path)}"
        dest = output_path if output_path else download_path

        dest.parent.mkdir(parents=True, exist_ok=True)
        click.echo(f"Downloading manifest to {dest}...")
        download_organization_artifact(
            key=key,
            path=dest,
            organization=organization,
            api_token=api_token,
        )
        click.echo("Download complete.")
