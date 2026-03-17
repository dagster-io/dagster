import os
from pathlib import Path

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config_utils import dg_api_options


@click.group(
    name="dbt",
    cls=DgClickGroup,
)
def dbt_group():
    """Commands for managing dbt integrations with Dagster Plus."""


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
    try:
        from dagster_dbt import DbtProject
    except ImportError:
        raise click.ClickException(
            "Unable to import dagster_dbt. To use `manage-manifest`, dagster-dbt must be installed."
        )

    from dagster_cloud_cli.commands.ci import state
    from dagster_cloud_cli.core.artifacts import (
        download_organization_artifact,
        upload_organization_artifact,
    )

    if not components_path and not file_path:
        raise click.UsageError("Must specify --components or --file.")

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

    # Discover DbtProject instances
    if file_path:
        from dagster._core.code_pointer import load_python_file
        from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types

        contents = load_python_file(file_path, None)
        projects = find_objects_in_module_of_types(contents, DbtProject)
    else:
        from dagster_dbt.components.dbt_project.component import get_projects_from_dbt_component

        assert components_path is not None  # guaranteed by earlier check
        projects = get_projects_from_dbt_component(components_path)

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
