import click

from create_dagster.cli.scaffold import scaffold_project_command, scaffold_workspace_command
from create_dagster.version import __version__

CREATE_DAGSTER_CLI_MAX_OUTPUT_WIDTH = 120


def get_create_dagster_cli():
    @click.group(
        name="create-dagster",
        commands={
            "project": scaffold_project_command,
            "workspace": scaffold_workspace_command,
        },
        context_settings={
            "max_content_width": CREATE_DAGSTER_CLI_MAX_OUTPUT_WIDTH,
            "help_option_names": ["-h", "--help"],
        },
    )
    @click.version_option(__version__, "--version", "-v")
    def group():
        """CLI for creating a new Dagster project or workspace."""

    return group


ENV_PREFIX = "CREATE_DAGSTER"
cli = get_create_dagster_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
