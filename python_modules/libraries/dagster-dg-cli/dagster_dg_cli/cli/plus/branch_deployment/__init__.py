"""Branch deployment command group for Dagster+."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.branch_deployment.commands import (
    create_or_update_command,
    delete_command,
)


@click.group(name="branch-deployment", cls=DgClickGroup)
def branch_deployment_group():
    """Manage branch deployments in Dagster+.

    Branch deployments are ephemeral environments that allow you to test code
    changes before merging to production. They are automatically created based
    on git branches and can include metadata about commits and pull requests.

    Use these commands to create, update, and delete branch deployments.
    """


# Register commands
branch_deployment_group.add_command(create_or_update_command)
branch_deployment_group.add_command(delete_command)
