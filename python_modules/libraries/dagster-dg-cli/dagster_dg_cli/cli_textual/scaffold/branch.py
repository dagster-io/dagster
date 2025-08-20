"""Textual-based scaffold branch command implementation."""

from typing import Optional

import click
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from textual import on
from textual.app import App
from textual.containers import Container
from textual.widgets import Input


class BranchDescriptionApp(App):
    """Simple Textual app with a text input at the top."""

    def compose(self):
        """Create child widgets for the app."""
        with Container():
            yield Input(placeholder="Enter branch description...", id="description_input")

    def on_mount(self):
        """Called when app starts."""
        self.query_one("#description_input", Input).focus()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted):
        """Handle when user presses Enter in the input."""
        description = event.value.strip()
        if description:
            click.echo(f"Description: {description}")
        self.exit(description if description else None)


def launch_web_interface() -> Optional[str]:
    """Print the textual run command for the web interface."""
    import os

    # Get the absolute path to the web_branch_app.py file
    current_dir = os.path.dirname(__file__)
    web_app_path = os.path.join(os.path.dirname(current_dir), "web_branch_app.py")

    click.echo(f"python -m textual run --dev {web_app_path}")
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
    **kwargs,
) -> None:
    """Scaffold a new branch using Textual interface.

    DESCRIPTION: Description of the branch to scaffold (optional).
    """
    if description is None:
        if web:
            # Print web interface command and exit
            launch_web_interface()
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
