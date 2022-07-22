from gzip import GzipFile
from typing import Tuple

import click
from tqdm import tqdm

from dagster import DagsterInstance
from dagster.core.debug import DebugRunPayload
from dagster.core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster.serdes import deserialize_as


def _recent_failed_runs_text(instance):
    lines = []
    runs = instance.get_runs(
        limit=5,
        filters=RunsFilter(statuses=[PipelineRunStatus.FAILURE, PipelineRunStatus.CANCELED]),
    )
    if len(runs) <= 0:
        return ""
    for run in runs:
        lines.append("{:<50}{:<50}{:<20}".format(run.run_id, run.pipeline_name, run.status))
    return "Recently failed runs:\n{}".format("\n".join(lines))


def export_run(instance, run, output_file):
    debug_payload = DebugRunPayload.build(instance, run)
    with GzipFile(output_file, "wb") as file:
        click.echo("Exporting run_id '{}' to gzip output file {}.".format(run.run_id, output_file))
        debug_payload.write(file)


@click.group(name="debug")
def debug_cli():
    """
    Commands for debugging Dagster pipeline/job runs.
    """


@debug_cli.command(
    name="export", help="Export the relevant artifacts for a pipeline/job run to a file."
)
@click.argument("run_id", type=str)
@click.argument("output_file", type=click.Path())
def export_command(run_id, output_file):

    with DagsterInstance.get() as instance:
        run = instance.get_run_by_id(run_id)
        if run is None:
            raise click.UsageError(
                "Could not find run with run_id '{}'.\n{}".format(
                    run_id, _recent_failed_runs_text(instance)
                )
            )

        export_run(instance, run, output_file)


@debug_cli.command(
    name="import", help="Import the relevant artifacts for a pipeline/job run from a file."
)
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
def import_command(input_files: Tuple[str, ...]):
    debug_payloads = []
    for input_file in input_files:
        with GzipFile(input_file, "rb") as file:
            blob = file.read().decode("utf-8")
            debug_payload = deserialize_as(blob, DebugRunPayload)
            debug_payloads.append(debug_payload)

    with DagsterInstance.get() as instance:
        for debug_payload in debug_payloads:
            run = debug_payload.pipeline_run
            click.echo(f"Importing run {run.run_id} (Dagster: {debug_payload.version})")
            if not instance.has_snapshot(run.execution_plan_snapshot_id):
                instance.add_snapshot(
                    debug_payload.execution_plan_snapshot,
                    run.execution_plan_snapshot_id,
                )
            if not instance.has_snapshot(run.pipeline_snapshot_id):
                instance.add_snapshot(
                    debug_payload.pipeline_snapshot,
                    run.pipeline_snapshot_id,
                )

            if not instance.has_run(run.run_id):
                instance.add_run(run)

                for event in tqdm(debug_payload.event_list):
                    instance.store_event(event)
