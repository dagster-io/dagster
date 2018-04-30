import click

import check


@click.command(name='create')
def dagster_pipeline_create_command():
    print('CREATE')


def define_pipeline_command_group():
    pipeline_command_group = click.Group(name='pipeline')
    pipeline_command_group.add_command(dagster_pipeline_create_command)
    return pipeline_command_group


def dagster_cli_main(argv):
    check.list_param(argv, 'argv', of_type=str)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(define_pipeline_command_group())
    dagster_command_group(argv[1:])
