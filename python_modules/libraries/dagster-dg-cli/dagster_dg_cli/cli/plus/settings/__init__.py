"""Settings command group for managing deployment settings in Dagster+."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.plus.settings.commands import (
    get_command,
    set_command,
    set_from_file_command,
)


@click.group(name="settings", cls=DgClickGroup)
def settings_group():
    """Manage deployment settings in Dagster+.

    Settings control deployment behavior including auto-materialization,
    run monitoring, retries, and more.
    """


settings_group.add_command(get_command)
settings_group.add_command(set_command)
settings_group.add_command(set_from_file_command)
