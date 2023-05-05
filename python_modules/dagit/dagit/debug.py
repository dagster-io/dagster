from gzip import GzipFile

import click
from dagster import (
    DagsterInstance,
)
from dagster._core.debug import DebugRunPayload
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._serdes.serdes import deserialize_value

from .cli import (
    DEFAULT_DAGIT_HOST,
    DEFAULT_DAGIT_PORT,
    host_dagit_ui_with_workspace_process_context,
)
from .version import __version__


@click.command(
    name="debug",
    help="Load dagit with an ephemeral instance loaded from a dagster debug export file.",
)
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--port",
    "-p",
    type=click.INT,
    help=f"Port to run server on, default is {DEFAULT_DAGIT_PORT}",
    default=DEFAULT_DAGIT_PORT,
)
def dagit_debug_command(input_files, port):
    debug_payloads = []
    for input_file in input_files:
        click.echo(f"Loading {input_file} ...")
        with GzipFile(input_file, "rb") as file:
            blob = file.read().decode("utf-8")
            debug_payload = deserialize_value(blob, DebugRunPayload)

            click.echo(
                "\trun_id: {} \n\tdagster version: {}".format(
                    debug_payload.dagster_run.run_id, debug_payload.version
                )
            )
            debug_payloads.append(debug_payload)

    instance = DagsterInstance.ephemeral(preload=debug_payloads)
    with WorkspaceProcessContext(instance, None, version=__version__) as workspace_process_context:
        host_dagit_ui_with_workspace_process_context(
            workspace_process_context=workspace_process_context,
            port=port,
            host=DEFAULT_DAGIT_HOST,
            path_prefix="",
            log_level="debug",
        )


def main():
    dagit_debug_command()
