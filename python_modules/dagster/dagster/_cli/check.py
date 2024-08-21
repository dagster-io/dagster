import logging
import os

import click

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


def check_command_options(f):
    return apply_click_params(
        f,
        workspace_option(),
        python_file_option(allow_multiple=True),
        python_module_option(allow_multiple=True),
    )


@check_command_options
@click.command(
    name="check",
    help="Validate if Dagster definitions are loadable.",
)
def check_command(**kwargs: ClickArgValue):
    logger = logging.getLogger("dagster")

    workspace_load_target = get_workspace_load_target(kwargs)
    workspace_origins = workspace_load_target.create_origins()

    # TODO: Allow another container image?
    container_image = os.getenv("DAGSTER_CURRENT_IMAGE")
    # TODO: Allow another entry point?
    entry_point = ["dagster"]

    for workspace_origin in workspace_origins:
        # TODO: What to do with ?
        if isinstance(workspace_origin, ManagedGrpcPythonEnvCodeLocationOrigin):
            # TODO: Raise exception is loadable_target_origin is None?

            logger.info("Starting check...")

            try:
                # TODO: Logging when loading the repository would be great, where should it be implemented?
                LoadedRepositories(
                    loadable_target_origin=workspace_origin.loadable_target_origin,
                    entry_point=entry_point,
                    container_image=container_image,
                )
            except Exception as e:
                print(e)
                pass

            logger.info("Ending check...")
