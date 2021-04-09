from gzip import GzipFile

import click
from dagster import DagsterInstance
from dagster.core.debug import DebugRunPayload
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter


def _recent_failed_runs_text(instance):
    lines = []
    runs = instance.get_runs(
        limit=5,
        filters=PipelineRunsFilter(
            statuses=[PipelineRunStatus.FAILURE, PipelineRunStatus.CANCELED]
        ),
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


def create_debug_cli_group():
    group = click.Group(name="debug")
    group.add_command(export_command)
    return group


@click.command(name="export", help="Export the relevant artifacts for a pipeline run to a file.")
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


debug_cli = create_debug_cli_group()
