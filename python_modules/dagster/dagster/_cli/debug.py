from gzip import GzipFile
from typing import List, Tuple

import click
from tqdm import tqdm

from dagster._core.debug import DebugRunPayload
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._serdes import deserialize_value

from .utils import get_instance_for_cli


def _recent_failed_runs_text(instance):
    lines = []
    runs = instance.get_runs(
        limit=5,
        filters=RunsFilter(statuses=[DagsterRunStatus.FAILURE, DagsterRunStatus.CANCELED]),
    )
    if len(runs) <= 0:
        return ""
    for run in runs:
        lines.append(f"{run.run_id:<50}{run.job_name:<50}{run.status:<20}")
    return "Recently failed runs:\n{}".format("\n".join(lines))


def export_run(instance, run, output_file):
    debug_payload = DebugRunPayload.build(instance, run)
    with GzipFile(output_file, "wb") as file:
        click.echo(f"Exporting run_id '{run.run_id}' to gzip output file {output_file}.")
        debug_payload.write(file)


@click.group(name="debug")
def debug_cli():
    """Commands for helping debug Dagster issues by dumping or loading artifacts from specific runs.

    This can be used to send a file to someone like the Dagster team who doesn't have direct access
    to your instance to allow them to view the events and details of a specific run.

    Debug files can be viewed using `dagster-webserver-debug` cli.
    Debug files can also be downloaded from the Dagster UI.
    """


@debug_cli.command(
    name="export",
    help="Export the relevant artifacts for a job run from the current instance in to a file.",
)
@click.argument("run_id", type=str)
@click.argument("output_file", type=click.Path())
def export_command(run_id, output_file):
    with get_instance_for_cli() as instance:
        run = instance.get_run_by_id(run_id)
        if run is None:
            raise click.UsageError(
                f"Could not find run with run_id '{run_id}'.\n{_recent_failed_runs_text(instance)}"
            )

        export_run(instance, run, output_file)


@debug_cli.command(
    name="import", help="Import the relevant artifacts from debug files in to the current instance."
)
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
def import_command(input_files: Tuple[str, ...]):
    debug_payloads: List[DebugRunPayload] = []
    for input_file in input_files:
        with GzipFile(input_file, "rb") as file:
            blob = file.read().decode("utf-8")
            debug_payload = deserialize_value(blob, DebugRunPayload)
            debug_payloads.append(debug_payload)

    with get_instance_for_cli() as instance:
        for debug_payload in debug_payloads:
            run = debug_payload.dagster_run
            click.echo(f"Importing run {run.run_id} (Dagster: {debug_payload.version})")
            if not instance.has_snapshot(run.execution_plan_snapshot_id):  # type: ignore  # (possible none)
                instance.add_snapshot(
                    debug_payload.execution_plan_snapshot,
                    run.execution_plan_snapshot_id,
                )
            if not instance.has_snapshot(run.job_snapshot_id):  # type: ignore  # (possible none)
                instance.add_snapshot(
                    debug_payload.job_snapshot,
                    run.job_snapshot_id,
                )

            if not instance.has_run(run.run_id):
                instance.add_run(run)

                for event in tqdm(debug_payload.event_list):
                    instance.store_event(event)
