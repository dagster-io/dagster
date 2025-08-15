import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.create.ci_api_token import create_ci_api_token
from dagster_dg_cli.cli.plus.create.env import create_env_command


@click.group(name="create", cls=DgClickGroup)
def plus_create_group():
    """Commands for creating configuration in Dagster Plus."""


plus_create_group.add_command(create_env_command)
plus_create_group.add_command(create_ci_api_token)
