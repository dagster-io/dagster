import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.config import plus_config_group
from dagster_dg_cli.cli.plus.create import plus_create_group
from dagster_dg_cli.cli.plus.deploy import deploy_group
from dagster_dg_cli.cli.plus.integrations import integrations_group
from dagster_dg_cli.cli.plus.login import login_command
from dagster_dg_cli.cli.plus.pull import plus_pull_group


@click.group(
    name="plus",
    cls=DgClickGroup,
    commands={
        "config": plus_config_group,
        "create": plus_create_group,
        "deploy": deploy_group,
        "integrations": integrations_group,
        "login": login_command,
        "pull": plus_pull_group,
    },
)
def plus_group():
    """Commands for interacting with Dagster Plus."""
