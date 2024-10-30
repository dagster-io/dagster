import logging
import os
import sys

import click

from dagster import __version__ as dagster_version
from dagster._cli.job import apply_click_params
from dagster._cli.utils import get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    ClickArgValue,
    get_workspace_from_kwargs,
    python_file_option,
    python_module_option,
    workspace_option,
)
from dagster._utils.log import configure_loggers


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
def definitions_validate_command(log_level: str, log_format: str, **kwargs: ClickArgValue):
    os.environ["DAGSTER_IS_DEFS_VALIDATION_CLI"] = "1"

    configure_loggers(formatter=log_format, log_level=log_level.upper())
    logger = logging.getLogger("dagster")

    logger.info("Starting validation...")
    with get_possibly_temporary_instance_for_cli(
        "dagster definitions validate", logger=logger
    ) as instance:
        with get_workspace_from_kwargs(
            instance=instance, version=dagster_version, kwargs=kwargs
        ) as workspace:
            invalid = any(
                entry
                for entry in workspace.get_code_location_entries().values()
                if entry.load_error
            )
            for code_location, entry in workspace.get_code_location_entries().items():
                if entry.load_error:
                    logger.error(
                        f"Validation failed for code location {code_location} with exception: "
                        f"{entry.load_error.message}."
                    )
                else:
                    logger.info(f"Validation successful for code location {code_location}.")
    logger.info("Ending validation...")
    sys.exit(0) if not invalid else sys.exit(1)
