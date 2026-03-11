import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.config.set import config_set_command
from dagster_dg_cli.cli.plus.config.view import config_view_command


@click.group(name="config", cls=DgClickGroup)
def plus_config_group():
    """Commands for viewing and managing Dagster Plus configuration."""


plus_config_group.add_command(config_set_command)
plus_config_group.add_command(config_view_command)
