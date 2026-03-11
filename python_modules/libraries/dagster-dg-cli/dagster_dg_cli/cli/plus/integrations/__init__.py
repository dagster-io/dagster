import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.integrations.dbt import dbt_group


@click.group(
    name="integrations",
    cls=DgClickGroup,
    commands={"dbt": dbt_group},
)
def integrations_group():
    """Commands for managing integrations with Dagster Plus."""
