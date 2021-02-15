from gzip import GzipFile

import click
from dagster import DagsterInstance, check
from dagster.cli.debug import DebugRunPayload
from dagster.cli.workspace import Workspace
from dagster.serdes import deserialize_json_to_dagster_namedtuple

from .cli import DEFAULT_DAGIT_HOST, DEFAULT_DAGIT_PORT, host_dagit_ui_with_workspace


@click.command(
    name="debug",
    help="Load dagit with an ephemeral instance loaded from a dagster debug export file.",
)
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--port",
    "-p",
    type=click.INT,
    help="Port to run server on, default is {default_port}".format(default_port=DEFAULT_DAGIT_PORT),
    default=DEFAULT_DAGIT_PORT,
)
def dagit_debug_command(input_files, port):
    debug_payloads = []
    for input_file in input_files:
        click.echo("Loading {} ...".format(input_file))
        with GzipFile(input_file, "rb") as file:
            blob = file.read().decode("utf-8")
            debug_payload = deserialize_json_to_dagster_namedtuple(blob)

            check.invariant(isinstance(debug_payload, DebugRunPayload))

            click.echo(
                "\trun_id: {} \n\tdagster version: {}".format(
                    debug_payload.pipeline_run.run_id, debug_payload.version
                )
            )
            debug_payloads.append(debug_payload)

    instance = DagsterInstance.ephemeral(preload=debug_payloads)
    host_dagit_ui_with_workspace(
        workspace=Workspace(None),
        instance=instance,
        port=port,
        port_lookup=True,
        host=DEFAULT_DAGIT_HOST,
        path_prefix="",
    )


def main():
    dagit_debug_command()  # pylint: disable=no-value-for-parameter
