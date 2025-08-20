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


@click.command(
    name="branch",
    cls=DgClickCommand,
)
@dg_path_options
@dg_global_options
@click.argument("description", required=False)
def scaffold_branch_command(
    description: Optional[str],
    **kwargs,
) -> None:
    """Scaffold a new branch using Textual interface.

    DESCRIPTION: Description of the branch to scaffold (optional).
    """
    if description is None:
        # Launch Textual app to get description
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
