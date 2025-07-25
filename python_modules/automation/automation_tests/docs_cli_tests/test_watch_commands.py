"""Tests for dagster-docs watch commands."""

import pytest
from automation.docs_cli.commands.watch import watch
from click.testing import CliRunner


class TestWatchCommands:
    """Test suite for watch commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_watch_help_command(self):
        """Test that watch help works."""
        result = self.runner.invoke(watch, ["--help"])

        assert result.exit_code == 0
        assert "Watch files for changes" in result.output
        assert "docstring" in result.output

    def test_watch_docstring_help_command(self):
        """Test that watch docstring help works."""
        result = self.runner.invoke(watch, ["docstring", "--help"])

        assert result.exit_code == 0
        assert "Watch docstring files for changes and validate them" in result.output
        assert "--symbol" in result.output
        assert "--changed" in result.output
        assert "--verbose" in result.output

    def test_watch_docstring_no_options_fails(self):
        """Test that watch docstring without options fails."""
        result = self.runner.invoke(watch, ["docstring"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: One of --changed or --symbol must be provided" in result.output

    def test_watch_docstring_multiple_options_fails(self):
        """Test that watch docstring with multiple options fails."""
        result = self.runner.invoke(watch, ["docstring", "--symbol", "dagster.asset", "--changed"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: Cannot use both --changed and --symbol together" in result.output

    def test_watch_docstring_changed_not_implemented(self):
        """Test that watch docstring --changed raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as excinfo:
            self.runner.invoke(watch, ["docstring", "--changed"], catch_exceptions=False)

        assert "Watching changed files functionality not yet fully implemented" in str(
            excinfo.value
        )

    # Note: We don't test --symbol functionality since it would actually start watching
    # and would be difficult to test in a unit test environment. The integration
    # of symbol resolution and file watching is tested by the existing watch functionality
    # and we test the helper functions individually.
