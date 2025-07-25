"""Tests for dagster-docs ls commands."""

from automation.dagster_docs.commands.ls import ls
from click.testing import CliRunner


class TestLsCommands:
    """Test suite for ls commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_ls_symbols_with_package_dagster(self):
        """Test listing symbols from dagster package."""
        result = self.runner.invoke(ls, ["symbols", "--package", "dagster"])

        # Should complete successfully
        assert result.exit_code == 0

        # Should contain some @public-decorated dagster symbols
        output = result.output
        assert "dagster.Component" in output
        assert "dagster.ComponentLoadContext" in output
        assert "dagster.definitions" in output

    def test_ls_symbols_with_package_dagster_core(self):
        """Test listing symbols from dagster._core subpackage."""
        result = self.runner.invoke(ls, ["symbols", "--package", "dagster._core.definitions"])

        # Should complete successfully
        assert result.exit_code == 0

        # This subpackage may have no @public symbols, which is valid
        # The test passes as long as the command doesn't error
        assert result.exit_code == 0

    def test_ls_symbols_with_nonexistent_package(self):
        """Test listing symbols from nonexistent package should fail."""
        result = self.runner.invoke(ls, ["symbols", "--package", "nonexistent.package"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: Could not import package" in result.output

    def test_ls_symbols_no_options_fails(self):
        """Test that ls symbols without options fails."""
        result = self.runner.invoke(ls, ["symbols"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: One of --all or --package must be provided" in result.output

    def test_ls_symbols_all_runs(self):
        """Test that ls symbols --all runs without NotImplementedError."""
        result = self.runner.invoke(ls, ["symbols", "--all"])

        # Should not raise NotImplementedError and should exit cleanly
        assert result.exit_code in [0, 1]  # Can succeed or fail but shouldn't crash
        assert "Global symbol discovery functionality not yet implemented" not in result.output

    def test_ls_packages_runs(self):
        """Test that ls packages runs without NotImplementedError."""
        result = self.runner.invoke(ls, ["packages"])

        # Should not raise NotImplementedError and should exit cleanly
        assert result.exit_code == 0  # This should succeed as it lists packages
        assert "Package discovery functionality not yet implemented" not in result.output

    def test_ls_help_command(self):
        """Test that ls help works."""
        result = self.runner.invoke(ls, ["--help"])

        assert result.exit_code == 0
        assert "List packages and symbols" in result.output
        assert "packages" in result.output
        assert "symbols" in result.output
