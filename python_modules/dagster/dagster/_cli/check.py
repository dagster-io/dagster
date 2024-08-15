import logging
import os
import sys

import click

import dagster._check as check
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.server import LoadedRepositories

from .job import apply_click_params
from .workspace.cli_target import (
    ClickArgValue,
    get_working_directory_from_kwargs,
    python_file_option,
    python_module_option,
    working_directory_option,
    workspace_option,
)


def check_command_options(f):
    return apply_click_params(
        f,
        workspace_option(),
        # TODO: Handle multiple files
        python_file_option(allow_multiple=False),
        python_module_option(allow_multiple=False),
        working_directory_option(),
    )


@check_command_options
@click.command(
    name="check",
    help="Load and check Dagster definitions and repositories.",
)
def check_command(**kwargs: ClickArgValue):
    logger = logging.getLogger("dagster")

    # TODO: Read from pyproject.toml or workspace.yaml if present

    # TODO: Allow another container image?
    container_image = os.getenv("DAGSTER_CURRENT_IMAGE")
    # TODO: Allow another entry point?
    entry_point = ["dagster"]

    loadable_target_origin = None
    if any(
        kwargs[key]
        for key in [
            "working_directory",
            "module_name",
            "python_file",
        ]
    ):
        # TODO: Handle multiple files by iterating
        # in the gRPC api CLI we never load more than one module or python file at a time
        module_name = check.opt_str_elem(kwargs, "module_name")
        python_file = check.opt_str_elem(kwargs, "python_file")

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute=None,
            working_directory=get_working_directory_from_kwargs(kwargs),
            module_name=module_name,
            python_file=python_file,
            package_name=None,
        )

    # TODO: Raise exception is loadable_target_origin is None?

    logger.info("Starting check...")

    # TODO: Logging when loading the repository would be great, where should it be implemented?
    LoadedRepositories(
        loadable_target_origin=loadable_target_origin,
        entry_point=entry_point,
        container_image=container_image,
    )

    logger.info("Ending check...")
