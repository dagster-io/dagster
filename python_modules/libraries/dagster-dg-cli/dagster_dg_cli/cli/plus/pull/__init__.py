import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.pull.env import pull_env_command


@click.group(name="pull", cls=DgClickGroup)
def plus_pull_group():
    """Commands for pulling configuration from Dagster Plus."""


plus_pull_group.add_command(pull_env_command)
