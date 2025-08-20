"""Textual-based scaffold branch command implementation."""

from typing import Optional

import click
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand

from dagster_dg_cli.cli_textual.branch_description_app import BranchDescriptionApp


def print_web_serve_command() -> Optional[str]:
    """Print the serve_app.py command for the web interface."""
    import os

    # Get the absolute path to the serve_app.py file
    current_dir = os.path.dirname(__file__)
    serve_app_path = os.path.join(os.path.dirname(current_dir), "serve_app.py")

    click.echo(f"python {serve_app_path}")
    return None


@click.command(
    name="branch",
    cls=DgClickCommand,
)
@dg_path_options
@dg_global_options
@click.option("--web", is_flag=True, help="Launch interface in web browser instead of terminal")
@click.argument("description", required=False)
def scaffold_branch_command(
    description: Optional[str],
    web: bool,
    **_kwargs,
) -> None:
    """Scaffold a new branch using Textual interface.

    DESCRIPTION: Description of the branch to scaffold (optional).
    """
    if description is None:
        if web:
            # Print web interface command and exit
            print_web_serve_command()
            return
        else:
            # Launch terminal interface
            app = BranchDescriptionApp()
            result = app.run()
            if result is None:
                click.echo("No description provided.")
                return
            description = result
    else:
        # Use provided description
        click.echo(f"Description: {description}")

    click.echo("🚧 Branch scaffolding implementation coming soon...")
