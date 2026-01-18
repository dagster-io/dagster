import click

from dagster._cli.api import api_cli
from dagster._cli.asset import asset_cli
from dagster._cli.code_server import code_server_cli
from dagster._cli.debug import debug_cli
from dagster._cli.definitions import definitions_cli
from dagster._cli.dev import dev_command
from dagster._cli.instance import instance_cli
from dagster._cli.job import job_cli
from dagster._cli.project import project_cli
from dagster._cli.run import run_cli
from dagster._cli.schedule import schedule_cli
from dagster._cli.sensor import sensor_cli
from dagster.version import __version__


def create_dagster_cli():
    commands = {
        "api": api_cli,
        "job": job_cli,
        "run": run_cli,
        "instance": instance_cli,
        "schedule": schedule_cli,
        "sensor": sensor_cli,
        "asset": asset_cli,
        "debug": debug_cli,
        "project": project_cli,
        "dev": dev_command,
        "code-server": code_server_cli,
        "definitions": definitions_cli,
    }

    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
    )
    @click.version_option(__version__, "--version", "-v")
    def group():
        """CLI tools for working with Dagster."""

    return group


ENV_PREFIX = "DAGSTER_CLI"
cli = create_dagster_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
