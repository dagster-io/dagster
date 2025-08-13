"""Main API group registration."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.api.deployment import deployment_group


@click.group(
    name="api",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "deployment": deployment_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
