import click

from dagster._core.origin import DEFAULT_DAGSTER_ENTRY_POINT
from dagster._core.remote_representation import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._grpc.server import LoadedRepositories

from .job import apply_click_params
from .workspace.cli_target import (
    ClickArgValue,
    get_workspace_load_target,
    python_file_option,
    python_module_option,
    workspace_option,
)


@click.group(name="definitions")
def definitions_cli():
    """Commands for working with Dagster definitions."""


def validate_command_options(f):
    return apply_click_params(
        f,
        workspace_option(),
        python_file_option(allow_multiple=True),
        python_module_option(allow_multiple=True),
    )


@validate_command_options
@definitions_cli.command(
    name="validate",
    help="Validate if Dagster definitions are loadable.",
)
def definitions_validate_command(**kwargs: ClickArgValue):
    workspace_load_target = get_workspace_load_target(kwargs)
    code_locations_origins = workspace_load_target.create_origins()

    click.echo("Starting validation...")
    for code_location_origin in code_locations_origins:
        # TODO clean isinstance
        if not isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin):
            continue

        curr_target_origin = (
            code_location_origin.loadable_target_origin.python_file
            or code_location_origin.loadable_target_origin.module_name
            or code_location_origin.loadable_target_origin.package_name
        )
        click.echo(f"Validating definitions in {curr_target_origin}.")
        try:
            LoadedRepositories(
                loadable_target_origin=code_location_origin.loadable_target_origin,
                entry_point=DEFAULT_DAGSTER_ENTRY_POINT,
            )
        except Exception as e:
            click.echo(
                click.style("Validation failed with exception: ", fg="red") + f"{e}.", err=True
            )
            exit(1)
        else:
            click.echo("Validation successful!")
    click.echo("Ending validation...")
    exit(0)
