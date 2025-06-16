from typing import Optional

import click
from dagster_shared.cli import workspace_options
from tqdm import tqdm

from dagster import __version__ as dagster_version
from dagster._cli.utils import assert_no_remaining_opts, get_instance_for_cli
from dagster._cli.workspace.cli_target import (
    RepositoryOpts,
    WorkspaceOpts,
    get_job_from_cli_opts,
    job_name_option,
    repository_options,
)


@click.group(name="run")
def run_cli():
    """Commands for working with Dagster job runs."""


@run_cli.command(name="list", help="List the runs in the current Dagster instance.")
@click.option("--limit", help="Only list a specified number of runs", default=None, type=int)
def run_list_command(limit: int) -> None:
    with get_instance_for_cli() as instance:
        for run in instance.get_runs(limit=limit):
            click.echo(f"Run: {run.run_id}")
            click.echo(f"     Job: {run.job_name}")


@run_cli.command(
    name="delete",
    help="Delete a run by id and its associated event logs. Warning: Cannot be undone",
)
@click.option("--force", "-f", is_flag=True, default=False, help="Skip prompt to delete run.")
@click.argument("run_id")
def run_delete_command(run_id: str, force: bool) -> None:
    with get_instance_for_cli() as instance:
        if not instance.has_run(run_id):
            raise click.ClickException(f"No run found with id {run_id}.")

        if force:
            should_delete_run = True
        else:
            confirmation = click.prompt(
                f"Are you sure you want to delete run {run_id} and its event logs? Type DELETE."
            )
            should_delete_run = confirmation == "DELETE"

        if should_delete_run:
            instance.delete_run(run_id)
            click.echo(f"Deleted run {run_id} and its event log entries.")
        else:
            raise click.ClickException("Exiting without deleting run.")


@run_cli.command(
    name="wipe", help="Eliminate all run history and event logs. Warning: Cannot be undone."
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Skip prompt to delete run history and event logs.",
)
def run_wipe_command(force: bool) -> None:
    if force:
        should_delete_run = True
    else:
        confirmation = click.prompt(
            "Are you sure you want to delete all run history and event logs? Type DELETE."
        )
        should_delete_run = confirmation == "DELETE"

    if should_delete_run:
        with get_instance_for_cli() as instance:
            instance.wipe()
        click.echo("Deleted all run history and event logs.")
    else:
        raise click.ClickException("Exiting without deleting all run history and event logs.")


@run_cli.command(
    name="migrate-repository",
    help="Migrate the run history for a job from a historic repository to its current repository.",
)
@click.option(
    "--from",
    "-f",
    "from_label",
    help="The repository from which to migrate (format: <repository_name>@<location_name>)",
)
@workspace_options
@repository_options
@job_name_option(name="job_name")
def run_migrate_command(from_label: str, job_name: Optional[str], **other_opts: object) -> None:
    from dagster._core.storage.dagster_run import RunsFilter
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage
    from dagster._core.storage.tags import REPOSITORY_LABEL_TAG

    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    repository_opts = RepositoryOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    if not from_label:
        raise click.UsageError("Must specify a --from repository label")

    if not is_valid_repo_label(from_label):
        raise click.UsageError(
            "`--from` argument must be of the format: <repository_name>@<location_name>"
        )

    with get_instance_for_cli() as instance:
        with get_job_from_cli_opts(
            instance,
            version=dagster_version,
            workspace_opts=workspace_opts,
            repository_opts=repository_opts,
            job_name=job_name,
        ) as remote_job:
            new_job_origin = remote_job.get_remote_origin()
            job_name = remote_job.name
            to_label = new_job_origin.repository_origin.get_label()

        if not to_label:
            raise click.UsageError("Must specify valid job targets to migrate history to.")

        if to_label == from_label:
            click.echo(f"Migrating runs from {from_label} to {to_label} is a no-op.")
            return

        records = instance.get_run_records(
            filters=RunsFilter(job_name=job_name, tags={REPOSITORY_LABEL_TAG: from_label})
        )

        if not records:
            click.echo(f"No runs found for {job_name} in {from_label}.")
            return

        if not isinstance(instance.run_storage, SqlRunStorage):
            raise click.UsageError("Run migration only applies to SQL-based run storage")

        count = len(records)
        confirmation = click.prompt(
            f"Are you sure you want to migrate the run history for {job_name} from {from_label} to"
            f" {to_label} ({count} runs)? Type MIGRATE"
        )
        should_migrate = confirmation == "MIGRATE"

        if should_migrate:
            for record in tqdm(records):
                instance.run_storage.replace_job_origin(record.dagster_run, new_job_origin)
            click.echo(f"Migrated the run history for {job_name} from {from_label} to {to_label}.")
        else:
            raise click.ClickException("Exiting without migrating.")


def is_valid_repo_label(label: str) -> bool:
    parts = label.split("@")
    return len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0
