import click

from dagster_dg.cli.generate import generate_cli
from dagster_dg.cli.info import info_cli
from dagster_dg.cli.list import list_cli
from dagster_dg.version import __version__


def create_dg_cli():
    commands = {
        "generate": generate_cli,
        "info": info_cli,
        "list": list_cli,
    }

    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
    )
    @click.version_option(__version__, "--version", "-v")
    def group():
        """CLI tools for working with Dagster components."""

    return group


ENV_PREFIX = "DAGSTER_DG"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
