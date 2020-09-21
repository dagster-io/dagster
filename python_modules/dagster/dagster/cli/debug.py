from collections import namedtuple
from gzip import GzipFile

import click

from dagster import DagsterInstance, check
from dagster.core.events.log import EventRecord
from dagster.core.snap import ExecutionPlanSnapshot, PipelineSnapshot
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.serdes import serialize_dagster_namedtuple, whitelist_for_serdes


@whitelist_for_serdes
class DebugRunPayload(
    namedtuple(
        "_DebugRunPayload",
        "version pipeline_run event_list pipeline_snapshot execution_plan_snapshot",
    )
):
    def __new__(
        cls, version, pipeline_run, event_list, pipeline_snapshot, execution_plan_snapshot,
    ):
        return super(DebugRunPayload, cls).__new__(
            cls,
            version=check.str_param(version, "version"),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            event_list=check.list_param(event_list, "event_list", EventRecord),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
            ),
            execution_plan_snapshot=check.inst_param(
                execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
            ),
        )


def _recent_failed_runs_text(instance):
    lines = []
    runs = instance.get_runs(limit=5, filters=PipelineRunsFilter(status=PipelineRunStatus.FAILURE))
    if len(runs) <= 0:
        return ""
    for run in runs:
        lines.append("{:<50}{:<50}{:<20}".format(run.run_id, run.pipeline_name, run.status))
    return "Recently failed runs:\n{}".format("\n".join(lines))


def create_debug_cli_group():
    group = click.Group(name="debug")
    group.add_command(export_command)
    return group


@click.command(name="export", help="Export the relevant artifacts for a pipeline run to a file.")
@click.argument("run_id", type=str)
@click.argument("output_file", type=click.Path())
def export_command(run_id, output_file):
    from dagster import __version__ as dagster_version

    with DagsterInstance.get() as instance:
        run = instance.get_run_by_id(run_id)
        if run is None:
            raise click.UsageError(
                "Could not find run with run_id '{}'.\n{}".format(
                    run_id, _recent_failed_runs_text(instance)
                )
            )
        events = instance.all_logs(run_id)
        debug_str = serialize_dagster_namedtuple(
            DebugRunPayload(
                version=dagster_version,
                pipeline_run=run,
                event_list=events,
                pipeline_snapshot=instance.get_pipeline_snapshot(run.pipeline_snapshot_id),
                execution_plan_snapshot=instance.get_execution_plan_snapshot(
                    run.execution_plan_snapshot_id
                ),
            )
        )
        with GzipFile(output_file, "wb") as file:
            click.echo("Exporting run_id '{}' to gzip output file {}.".format(run_id, output_file))
            file.write(debug_str.encode())


debug_cli = create_debug_cli_group()
