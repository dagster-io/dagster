"""Tests for dagster-docs watch commands."""

from automation.dagster_docs.commands.watch import watch
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
        assert "docstrings" in result.output

    def test_watch_docstrings_help_command(self):
        """Test that watch docstrings help works."""
        result = self.runner.invoke(watch, ["docstrings", "--help"])

        assert result.exit_code == 0
        assert "Watch docstring files for changes and validate them" in result.output
        assert "--symbol" in result.output
        assert "--changed" in result.output
        assert "--verbose" in result.output

    def test_watch_docstrings_no_options_fails(self):
        """Test that watch docstrings without options fails."""
        result = self.runner.invoke(watch, ["docstrings"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: One of --changed or --symbol must be provided" in result.output

    def test_watch_docstrings_multiple_options_fails(self):
        """Test that watch docstrings with multiple options fails."""
        result = self.runner.invoke(watch, ["docstrings", "--symbol", "dagster.asset", "--changed"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: Cannot use both --changed and --symbol together" in result.output

    def test_watch_docstrings_changed_option_available(self):
        """Test that watch docstrings --changed option is available in help."""
        result = self.runner.invoke(watch, ["docstrings", "--help"])

        assert result.exit_code == 0
        assert "--changed" in result.output
        assert "Watches the files currently changed in git" in result.output

    # Note: We don't test --symbol functionality since it would actually start watching
    # and would be difficult to test in a unit test environment. The integration
    # of symbol resolution and file watching is tested by the existing watch functionality
    # and we test the helper functions individually.
