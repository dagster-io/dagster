import click

from dagster.core.instance import DagsterInstance


def create_run_cli_group():
    group = click.Group(name='run')
    group.add_command(run_list_command)
    group.add_command(run_wipe_command)
    return group


@click.command(name='list', help='List the runs in this dagster installation.')
def run_list_command():
    instance = DagsterInstance.get()
    for run in instance.all_runs:
        click.echo('Run: {}'.format(run.run_id))
        click.echo('     Pipeline: {}'.format(run.pipeline_name))


@click.command(name='wipe', help='Eliminate all run history. Warning: Cannot be undone')
def run_wipe_command():
    instance = DagsterInstance.get()
    instance.wipe()
    click.echo('Deleted all run history')
