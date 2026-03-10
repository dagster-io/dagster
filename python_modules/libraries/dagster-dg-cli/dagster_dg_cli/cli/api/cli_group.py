"""Main API group registration."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.api.agent import agent_group
from dagster_dg_cli.cli.api.asset import asset_group
from dagster_dg_cli.cli.api.code_location import code_location_group
from dagster_dg_cli.cli.api.deployment import deployment_group
from dagster_dg_cli.cli.api.issues import issue_group
from dagster_dg_cli.cli.api.organization import organization_group
from dagster_dg_cli.cli.api.run import run_group
from dagster_dg_cli.cli.api.schedule import schedule_group
from dagster_dg_cli.cli.api.secret import secret_group
from dagster_dg_cli.cli.api.sensor import sensor_group


@click.group(
    name="api",
    cls=DgClickGroup,
    commands={
        "agent": agent_group,
        "asset": asset_group,
        "code-location": code_location_group,
        "deployment": deployment_group,
        "issue": issue_group,
        "organization": organization_group,
        "run": run_group,
        "schedule": schedule_group,
        "secret": secret_group,
        "sensor": sensor_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
