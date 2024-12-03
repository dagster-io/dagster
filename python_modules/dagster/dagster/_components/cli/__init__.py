import click

from dagster._components.cli.generate import generate_cli
from dagster.version import __version__


def create_dagster_components_cli():
    commands = {
        "generate": generate_cli,
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
cli = create_dagster_components_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
