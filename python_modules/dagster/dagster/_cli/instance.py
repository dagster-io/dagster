import os

import click

import dagster._check as check
from dagster._cli.utils import get_instance_for_cli
from dagster._core.instance import DagsterInstance
from dagster._core.storage.migration.bigint_migration import run_bigint_migration


@click.group(name="instance")
def instance_cli():
    """Commands for working with the current Dagster instance."""


@instance_cli.command(name="info", help="List the information about the current instance.")
def info_command():
    with get_instance_for_cli() as instance:
        home = os.environ.get("DAGSTER_HOME")

        if instance.is_ephemeral:
            check.invariant(
                home is None,
                f'Unexpected state, ephemeral instance but DAGSTER_HOME is set to "{home}"',
            )
            click.echo(
                "$DAGSTER_HOME is not set, using an ephemeral instance. "
                "Run artifacts will only exist in memory and any filesystem access "
                "will use a temp directory that gets cleaned up on exit."
            )
            return

        click.echo(f"$DAGSTER_HOME: {home}\n")

        click.echo("\nInstance configuration:\n-----------------------")
        click.echo(instance.info_str())

        click.echo("\nStorage schema state:\n---------------------")
        click.echo(instance.schema_str())


@instance_cli.command(name="migrate", help="Automatically migrate an out of date instance.")
@click.option("--bigint-migration", is_flag=True, help="Run an optional bigint migration")
def migrate_command(**kwargs):
    if kwargs.get("bigint_migration"):
        _run_bigint_migration()
        return

    with get_instance_for_cli() as instance:
        home = os.environ.get("DAGSTER_HOME")
        if not home:
            click.echo("$DAGSTER_HOME is not set; ephemeral instances do not need to be migrated.")
            return

        click.echo(f"$DAGSTER_HOME: {home}\n")

        click.echo("\nInstance configuration:\n-----------------------")
        click.echo(instance.info_str())

        click.echo(
            "\nStorage schema state before migration:\n--------------------------------------"
        )
        click.echo(instance.schema_str())

        click.echo("\nRunning migration:\n------------------")

        instance.upgrade(click.echo)

        click.echo("\nStorage schema state after migration:\n-------------------------------------")
        click.echo(instance.schema_str())


@instance_cli.command(name="reindex", help="Rebuild index over historical runs for performance.")
def reindex_command():
    with get_instance_for_cli() as instance:
        home = os.environ.get("DAGSTER_HOME")

        if instance.is_ephemeral:
            click.echo(
                "$DAGSTER_HOME is not set; ephemeral instances cannot be reindexed.  If you "
                "intended to migrate a persistent instance, please ensure that $DAGSTER_HOME is "
                "set accordingly."
            )
            return

        click.echo(f"$DAGSTER_HOME: {home}\n")

        instance.reindex(click.echo)


@instance_cli.group(name="concurrency")
def concurrency_cli():
    """Commands for working with the instance-wide op concurrency."""


@concurrency_cli.command(name="get", help="Get op concurrency limits")
@click.option(
    "--all",
    required=False,
    is_flag=True,
    help="Get info on all instance op concurrency limits",
)
@click.argument("key", required=False)
def get_concurrency(key, **kwargs):
    with DagsterInstance.get() as instance:
        check_concurrency_support(instance)
        if kwargs.get("all"):
            keys = instance.event_log_storage.get_concurrency_keys()
            if not keys:
                click.echo(
                    "No concurrency limits set. Run `dagster instance concurrency set <key>"
                    " <limit>` to set limits."
                )
            else:
                click.echo("Concurrency limits:")
                for key in keys:
                    concurrency_print_key(instance, key)
        elif key:
            concurrency_print_key(instance, key)
        else:
            raise click.ClickException(
                "Must either specify a key argument or the `--all` option. Run `dagster instance "
                "concurrency get --help` for more info."
            )


def concurrency_print_key(instance: DagsterInstance, key: str):
    key_info = instance.event_log_storage.get_concurrency_info(key)
    click.echo(f'"{key}": {len(key_info.claimed_slots)} / {key_info.slot_count} slots occupied')


@concurrency_cli.command(name="set", help="Set op concurrency limits")
@click.argument("key", required=True)
@click.argument("limit", required=True, type=click.INT)
def set_concurrency(key, limit):
    with DagsterInstance.get() as instance:
        check_concurrency_support(instance)
        instance.event_log_storage.set_concurrency_slots(key, limit)
        click.echo(f"Set concurrency limit for {key} to {limit}.")


def check_concurrency_support(instance: DagsterInstance):
    from dagster._core.storage.event_log.sqlite.sqlite_event_log import SqliteEventLogStorage

    if instance.event_log_storage.supports_global_concurrency_limits:
        return

    if isinstance(instance.event_log_storage, SqliteEventLogStorage):
        raise click.ClickException(
            "This instance storage does not support global concurrency limits. You will need "
            "to configure a different storage implementation (e.g. Postgres/MySQL) to use this "
            "feature."
        )

    # not a sqlite storage, but may not have run `dagster instance migrate` to add the tables for
    # concurrency support
    raise click.ClickException(
        "This instance storage does not currently support global concurrency limits. You may need "
        "to run `dagster instance migrate` to add the necessary tables in your dagster storage to "
        "support this feature."
    )


def _run_bigint_migration():
    with get_instance_for_cli() as instance:
        home = os.environ.get("DAGSTER_HOME")
        if not home:
            click.echo("$DAGSTER_HOME is not set; ephemeral instances do not need to be migrated.")
            return

        confirmation = click.prompt(
            "Are you sure you want to migrate all your id cols from int to bigint? This may lock "
            "tables for an extended period of time while the migration is under way. Type MIGRATE "
            "to confirm"
        )

        if confirmation == "MIGRATE":
            run_bigint_migration(instance, click.echo)
        else:
            click.echo("Exiting without running bigint migration")
