import click

from dg_cli.cli.generate import generate_cli
from dg_cli.cli.list import list_cli
from dg_cli.version import __version__


def create_dg_cli():
    commands = {
        "generate": generate_cli,
        "list": list_cli,
    }

    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
    )
    @click.version_option(__version__, "--version", "-v")
    def group():
        """CLI tools for working with Dagster."""

    return group


ENV_PREFIX = "DG_CLI"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
