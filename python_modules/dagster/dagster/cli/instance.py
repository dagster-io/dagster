import os

import click
from dagster import check
from dagster.core.instance import DagsterInstance


def create_instance_cli_group():
    group = click.Group(name="instance")
    group.add_command(info_command)
    group.add_command(migrate_command)
    group.add_command(reindex_command)
    return group


@click.command(name="info", help="List the information about the current instance.")
def info_command():
    with DagsterInstance.get() as instance:
        home = os.environ.get("DAGSTER_HOME")

        if instance.is_ephemeral:
            check.invariant(
                home is None,
                'Unexpected state, ephemeral instance but DAGSTER_HOME is set to "{}"'.format(home),
            )
            click.echo(
                "$DAGSTER_HOME is not set, using an ephemeral instance. "
                "Run artifacts will only exist in memory and any filesystem access "
                "will use a temp directory that gets cleaned up on exit."
            )
            return

        click.echo("$DAGSTER_HOME: {}\n".format(home))

        click.echo(instance.info_str())


@click.command(name="migrate", help="Automatically migrate an out of date instance.")
def migrate_command():
    home = os.environ.get("DAGSTER_HOME")
    if not home:
        click.echo("$DAGSTER_HOME is not set; ephemeral instances do not need to be migrated.")

    click.echo("$DAGSTER_HOME: {}\n".format(home))

    with DagsterInstance.get() as instance:
        instance.upgrade(click.echo)

        click.echo(instance.info_str())


@click.command(name="reindex", help="Rebuild index over historical runs for performance.")
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

        click.echo("$DAGSTER_HOME: {}\n".format(home))

        instance.reindex(click.echo)


instance_cli = create_instance_cli_group()
