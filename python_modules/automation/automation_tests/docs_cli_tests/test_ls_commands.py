"""Tests for dagster-docs ls commands."""

import pytest
from automation.docs_cli.commands.ls import ls
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

        # Should contain some well-known dagster symbols
        output = result.output
        assert "dagster.asset" in output
        assert "dagster.op" in output
        assert "dagster.job" in output

    def test_ls_symbols_with_package_dagster_core(self):
        """Test listing symbols from dagster._core subpackage."""
        result = self.runner.invoke(ls, ["symbols", "--package", "dagster._core.definitions"])

        # Should complete successfully
        assert result.exit_code == 0

        # Should contain some symbols (exact content may vary)
        assert len(result.output.strip()) > 0

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

    def test_ls_symbols_all_not_implemented(self):
        """Test that ls symbols --all raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as excinfo:
            self.runner.invoke(ls, ["symbols", "--all"], catch_exceptions=False)

        assert "Global symbol discovery functionality not yet implemented" in str(excinfo.value)

    def test_ls_packages_not_implemented(self):
        """Test that ls packages raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as excinfo:
            self.runner.invoke(ls, ["packages"], catch_exceptions=False)

        assert "Package discovery functionality not yet implemented" in str(excinfo.value)

    def test_ls_help_command(self):
        """Test that ls help works."""
        result = self.runner.invoke(ls, ["--help"])

        assert result.exit_code == 0
        assert "List packages and symbols" in result.output
        assert "packages" in result.output
        assert "symbols" in result.output
