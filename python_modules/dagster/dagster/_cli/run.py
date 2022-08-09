import click
from tqdm import tqdm

from dagster._core.instance import DagsterInstance


@click.group(name="run")
def run_cli():
    """
    Commands for working with Dagster job runs.
    """


@run_cli.command(name="list", help="List the runs in the current Dagster instance.")
@click.option("--limit", help="Only list a specified number of runs", default=None, type=int)
def run_list_command(limit):
    with DagsterInstance.get() as instance:
        for run in instance.get_runs(limit=limit):
            click.echo("Run: {}".format(run.run_id))
            click.echo("     Job: {}".format(run.pipeline_name))


@run_cli.command(
    name="delete",
    help="Delete a run by id and its associated event logs. Warning: Cannot be undone",
)
@click.option("--force", "-f", is_flag=True, default=False, help="Skip prompt to delete run.")
@click.argument("run_id")
def run_delete_command(run_id, force):
    with DagsterInstance.get() as instance:
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
def run_wipe_command(force):
    if force:
        should_delete_run = True
    else:
        confirmation = click.prompt(
            "Are you sure you want to delete all run history and event logs? Type DELETE."
        )
        should_delete_run = confirmation == "DELETE"

    if should_delete_run:
        with DagsterInstance.get() as instance:
            instance.wipe()
        click.echo("Deleted all run history and event logs.")
    else:
        raise click.ClickException("Exiting without deleting all run history and event logs.")


@run_cli.command(name="migrate", help="Migrate the run history from one repository to another.")
@click.option(
    "--from",
    "-f",
    "from_label",
    help="The repository from which to migrate (format: <repository_name>@<location_name>)",
    prompt_required=True,
)
@click.option(
    "--to",
    "-t",
    "to_label",
    help="The repository name to migrate to (format: <repository_name>@<location_name>)",
    prompt_required=True,
)
@click.argument("job_name")
def run_migrate_command(job_name, from_label, to_label):
    from dagster._core.storage.pipeline_run import RunsFilter
    from dagster._core.storage.runs.schema import RunTagsTable
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage
    from dagster._core.storage.tags import REPOSITORY_LABEL_TAG

    if not from_label or not to_label:
        raise click.UsageError("Please specify both a --from and --to repository label")

    if not is_valid_repo_label(from_label) or not is_valid_repo_label(to_label):
        raise click.UsageError(
            "`--from` and `--to` arguments must be of the format: <repository_name>@<location_name>"
        )

    with DagsterInstance.get() as instance:
        records = instance.get_run_records(
            filters=RunsFilter(job_name=job_name, tags={REPOSITORY_LABEL_TAG: from_label})
        )

        if not records:
            click.echo(f"No runs found for {job_name} in {from_label}.")
            return

        if not isinstance(instance.run_storage, SqlRunStorage):
            return

        count = len(records)
        confirmation = click.prompt(
            f"Are you sure you want to migrate the run history for {job_name} ({count} runs)? Type MIGRATE"
        )
        should_migrate = confirmation == "MIGRATE"

        if should_migrate:
            for record in tqdm(records):
                with instance.run_storage.connect() as conn:
                    conn.execute(
                        RunTagsTable.update()  # pylint: disable=no-value-for-parameter
                        .where(RunTagsTable.c.run_id == record.pipeline_run.run_id)
                        .where(RunTagsTable.c.key == REPOSITORY_LABEL_TAG)
                        .values(value=to_label)
                    )
            click.echo(f"Migrated the run history for {job_name} from {from_label} to {to_label}.")
        else:
            raise click.ClickException("Exiting without migrating.")


def is_valid_repo_label(label):
    parts = label.split("@")
    return len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0
