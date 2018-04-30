import click

import check


def dagster_cli_main(argv):
    check.list_param(argv, 'argv', of_type=str)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group(argv[1:])
