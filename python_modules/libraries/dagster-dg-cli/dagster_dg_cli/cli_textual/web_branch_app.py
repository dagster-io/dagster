"""Standalone Textual app for web-based branch description input.

Usage:
    textual serve dagster_dg_cli.cli_textual.web_branch_app:app --port 8000

Then visit http://127.0.0.1:8000 in your browser.
"""

from textual import on
from textual.app import App
from textual.containers import Container, Vertical
from textual.css.query import NoMatches
from textual.widgets import Button, Input, Static


class WebBranchApp(App):
    """Web-based branch description input app."""

    CSS = """
    Container {
        align: center middle;
        width: 60%;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }
    
    Static#title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    Static#prompt {
        text-align: center;
        margin-bottom: 1;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    
    Static#result {
        text-align: center;
        text-style: bold;
        color: $success;
        margin-top: 1;
    }
    """

    def compose(self):
        """Create child widgets for the app."""
        with Container():
            with Vertical():
                yield Static("🚀 Branch Description", id="title")
                yield Static("Enter a description for your new branch:", id="prompt")
                yield Input(placeholder="Enter branch description...", id="description_input")
                yield Button("Create Branch", variant="primary", id="submit_btn")

    def on_mount(self):
        """Called when app starts."""
        self.query_one("#description_input", Input).focus()

    @on(Button.Pressed, "#submit_btn")
    def on_submit_pressed(self):
        """Handle submit button press."""
        input_widget = self.query_one("#description_input", Input)
        description = input_widget.value.strip()
        if description:
            self.handle_submission(description)

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted):
        """Handle when user presses Enter in the input."""
        description = event.value.strip()
        if description:
            self.handle_submission(description)

    def handle_submission(self, description: str):
        """Handle the description submission."""
        # Update UI to show success
        try:
            prompt_widget = self.query_one("#prompt")
            prompt_widget.update("✅ Branch description submitted successfully!")
            prompt_widget.add_class("result")
        except NoMatches:
            pass

        try:
            input_widget = self.query_one("#description_input", Input)
            input_widget.value = description
            input_widget.disabled = True
        except NoMatches:
            pass

        try:
            button_widget = self.query_one("#submit_btn", Button)
            button_widget.disabled = True
        except NoMatches:
            pass

        # Store result for external access
        self.description_result = description


# Create the app instance that textual serve can use
app = WebBranchApp()

if __name__ == "__main__":
    # For direct running (not via textual serve)
    result = app.run()
    # Result is stored in app.description_result for external access
