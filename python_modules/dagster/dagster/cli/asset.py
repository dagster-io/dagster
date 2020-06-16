import click

from dagster.core.instance import DagsterInstance


def create_asset_cli_group():
    group = click.Group(name='asset')
    group.add_command(asset_wipe_command)
    return group


@click.command(
    name='wipe', help='Eliminate all asset key indexes from event logs. Warning: Cannot be undone'
)
def asset_wipe_command():
    confirmation = click.prompt(
        'Are you sure you want to remove all asset key indexes from the event logs? Type DELETE'
    )
    if confirmation == 'DELETE':
        instance = DagsterInstance.get()
        instance.wipe_assets()
        click.echo('Removed all asset indexes from event logs')
    else:
        click.echo('Exiting without removing asset indexes')


asset_cli = create_asset_cli_group()
