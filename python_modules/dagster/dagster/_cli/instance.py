import os

import click

import dagster._check as check
from dagster._core.instance import DagsterInstance


@click.group(name="instance")
def instance_cli():
    """Commands for working with the current Dagster instance."""


@instance_cli.command(name="info", help="List the information about the current instance.")
def info_command():
    with DagsterInstance.get() as instance:
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
def migrate_command():
    home = os.environ.get("DAGSTER_HOME")
    if not home:
        click.echo("$DAGSTER_HOME is not set; ephemeral instances do not need to be migrated.")

    click.echo(f"$DAGSTER_HOME: {home}\n")

    with DagsterInstance.get() as instance:
        instance.upgrade(click.echo)

        click.echo(instance.info_str())


@instance_cli.command(name="reindex", help="Rebuild index over historical runs for performance.")
def reindex_command():
    with DagsterInstance.get() as instance:
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
