"""API commands for interacting with Dagster Plus REST-like interface."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.api.deployments import deployments_group


@click.group(
    name="api",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "deployments": deployments_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
