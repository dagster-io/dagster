"""Textual app for branch description input."""

import click
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


# Create the app instance that can be used externally
app = BranchDescriptionApp()

if __name__ == "__main__":
    result = app.run()
