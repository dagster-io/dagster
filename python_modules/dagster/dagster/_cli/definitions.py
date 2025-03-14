import logging
import os
import sys

import click

from dagster import __version__ as dagster_version
from dagster._cli.utils import assert_no_remaining_opts, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    WorkspaceOpts,
    get_workspace_from_cli_opts,
    workspace_options,
)
from dagster._utils.error import remove_system_frames_from_error, unwrap_user_code_error
from dagster._utils.log import configure_loggers


@click.group(name="definitions")
def definitions_cli():
    """Commands for working with Dagster definitions."""


@workspace_options
@click.option(
    "--log-level",
    help="Set the log level for dagster services.",
    show_default=True,
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
)
@click.option(
    "--log-format",
    type=click.Choice(["colored", "json", "rich"], case_sensitive=False),
    show_default=True,
    required=False,
    default="colored",
    help="Format of the logs for dagster services",
)
@click.option(
    "--load-with-grpc",
    flag_value=True,
    default=False,
    help="Load the code locations using a gRPC server, instead of in-process.",
)
@click.option(
    "--verbose",
    "-v",
    flag_value=True,
    default=False,
    help="Show verbose stack traces, including system frames in stack traces.",
)
@definitions_cli.command(
    name="validate",
    help="""
    The `dagster definitions validate` command loads and validate your Dagster definitions using a Dagster instance.

    This command indicates which code locations contain errors, and which ones can be successfully loaded.
    Code locations containing errors are considered invalid, otherwise valid.

    When running, this command sets the environment variable `DAGSTER_IS_DEFS_VALIDATION_CLI=1`.
    This environment variable can be used to control the behavior of your code in validation mode.

    This command returns an exit code 1 when errors are found, otherwise an exit code 0.

    This command should be run in a Python environment where the `dagster` package is installed.
    """,
)
def definitions_validate_command(
    log_level: str,
    log_format: str,
    load_with_grpc: bool,
    verbose: bool,
    **other_opts: object,
):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)
    os.environ["DAGSTER_IS_DEFS_VALIDATION_CLI"] = "1"

    configure_loggers(formatter=log_format, log_level=log_level.upper())
    logger = logging.getLogger("dagster")
    logging.captureWarnings(True)

    removed_system_frame_hint = (
        lambda is_first_hidden_frame,
        i: f"  [{i} dagster system frames hidden, run with --verbose to see the full stack trace]\n"
        if is_first_hidden_frame
        else f"  [{i} dagster system frames hidden]\n"
    )

    with get_possibly_temporary_instance_for_cli(
        "dagster definitions validate", logger=logger
    ) as instance:
        with get_workspace_from_cli_opts(
            instance=instance,
            version=dagster_version,
            workspace_opts=workspace_opts,
            allow_in_process=not load_with_grpc,
            log_level=log_level,
        ) as workspace:
            if logger.parent:
                logger.parent.handlers.clear()
            invalid_locations = [
                entry
                for entry in workspace.get_code_location_entries().values()
                if entry.load_error
            ]
            for code_location, entry in workspace.get_code_location_entries().items():
                if entry.load_error:
                    if verbose:
                        underlying_error = entry.load_error
                    else:
                        underlying_error = remove_system_frames_from_error(
                            unwrap_user_code_error(entry.load_error),
                            build_system_frame_removed_hint=removed_system_frame_hint,
                        )
                    logger.error(
                        f"Validation failed for code location {code_location}:\n\n"
                        f"{underlying_error.to_string()}"
                    )
                    pass
                else:
                    logger.info(f"Validation successful for code location {code_location}.")

    if invalid_locations:
        logger.error(f"Validation for {len(invalid_locations)} code locations failed.")
        sys.exit(1)
    else:
        logger.info("All code locations passed validation.")
