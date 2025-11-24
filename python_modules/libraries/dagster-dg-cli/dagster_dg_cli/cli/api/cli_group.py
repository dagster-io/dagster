"""Main API group registration."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.api.agent import agent_group
from dagster_dg_cli.cli.api.asset import asset_group
from dagster_dg_cli.cli.api.deployment import deployment_group
from dagster_dg_cli.cli.api.log import log_group
from dagster_dg_cli.cli.api.run import run_group
from dagster_dg_cli.cli.api.run_event import run_events_group
from dagster_dg_cli.cli.api.schedule import schedule_group
from dagster_dg_cli.cli.api.secret import secret_group
from dagster_dg_cli.cli.api.sensor import sensor_group


@click.group(
    name="api",
    cls=DgClickGroup,
    commands={
        "agent": agent_group,
        "asset": asset_group,
        "deployment": deployment_group,
        "log": log_group,
        "run": run_group,
        "run-events": run_events_group,
        "schedule": schedule_group,
        "secret": secret_group,
        "sensor": sensor_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
