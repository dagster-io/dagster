import click

import check


@click.command(name='create')
@click.pass_context
def dagster_pipeline_create_command(ctx):
    print('CREATE')
    print(ctx.obj)


def define_pipeline_command_group():
    pipeline_command_group = click.Group(name='pipeline')
    pipeline_command_group.add_command(dagster_pipeline_create_command)
    return pipeline_command_group


def dagster_cli_main(argv, pipeline=None):
    check.list_param(argv, 'argv', of_type=str)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(define_pipeline_command_group())
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})
