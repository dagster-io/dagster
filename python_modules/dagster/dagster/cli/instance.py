import os

import click

from dagster import check
from dagster.core.instance import DagsterInstance


def create_instance_cli_group():
    group = click.Group(name='instance')
    group.add_command(info_command)
    group.add_command(migrate_command)
    return group


@click.command(name='info', help='List the information about the current instance.')
def info_command():
    instance = DagsterInstance.get()
    home = os.environ.get('DAGSTER_HOME')

    if instance.is_ephemeral:
        check.invariant(
            home is None,
            'Unexpected state, ephemeral instance but DAGSTER_HOME is set to "{}"'.format(home),
        )
        click.echo(
            '$DAGSTER_HOME is not set, using an ephemeral instance. '
            'Run artifacts will only exist in memory and any filesystem access '
            'will use a temp directory that gets cleaned up on exit.'
        )
        return

    click.echo('$DAGSTER_HOME: {}\n'.format(home))

    click.echo(instance.info_str())


@click.command(name='migrate', help='Automatically migrate an out of date instance.')
def migrate_command():
    instance = DagsterInstance.get()
    home = os.environ.get('DAGSTER_HOME')

    if instance.is_ephemeral:
        click.echo('$DAGSTER_HOME is not set; ephemeral instances do not need to be migrated.')
        return

    click.echo('$DAGSTER_HOME: {}\n'.format(home))

    instance.upgrade(click.echo)

    click.echo(instance.info_str())


instance_cli = create_instance_cli_group()
