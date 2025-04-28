import click

from dagster.components.cli.list import list_cli
from dagster.components.cli.scaffold import scaffold_cli
from dagster.version import __version__


def create_dagster_components_cli():
    commands = {
        "scaffold": scaffold_cli,
        "list": list_cli,
    }

    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
    )
    @click.version_option(__version__, "--version", "-v")
    def group():
        """Internal API for working with Dagster Components.

        This CLI is private and can be considered an implementation detail for `dg`. It is called by
        `dg` to execute commands related to Dagster Components in the context of a particular Python
        environment. This is necessary because `dg` itself always runs in an isolated environment.
        """

    return group


ENV_PREFIX = "DG_CLI"
cli = create_dagster_components_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
