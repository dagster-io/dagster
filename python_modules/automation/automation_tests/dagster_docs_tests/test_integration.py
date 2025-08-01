"""Integration tests for dagster-docs CLI."""

import pytest
from automation.dagster_docs.main import main
from click.testing import CliRunner


class TestMainCLIIntegration:
    """Integration tests for the main CLI entry point."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_help_command(self):
        """Test that main CLI help works."""
        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Dagster documentation tools" in result.output
        assert "ls" in result.output
        assert "check" in result.output
        assert "watch" in result.output

    def test_main_ls_symbols_integration(self):
        """Test complete ls symbols command through main CLI."""
        result = self.runner.invoke(main, ["ls", "symbols", "--package", "dagster"])

        assert result.exit_code == 0
        assert "dagster.Component" in result.output

    def test_main_check_docstrings_symbol_integration(self):
        """Test complete check docstrings command through main CLI."""
        result = self.runner.invoke(main, ["check", "docstrings", "--symbol", "dagster.asset"])

        assert result.exit_code == 0
        assert "Validating docstring for: dagster.asset" in result.output

    def test_main_check_docstrings_package_integration(self):
        """Test complete check docstrings package command through main CLI."""
        result = self.runner.invoke(
            main, ["check", "docstrings", "--package", "automation.dagster_docs"]
        )

        assert result.exit_code == 0
        assert "Validating" in result.output
        assert "public symbols in automation.dagster_docs" in result.output

    def test_main_invalid_command_fails(self):
        """Test that invalid commands fail gracefully."""
        result = self.runner.invoke(main, ["invalid-command"])

        assert result.exit_code == 2  # Click's standard exit code for usage errors
        assert "No such command" in result.output or "Usage:" in result.output


class TestRealDagsterSymbols:
    """Test against real Dagster symbols to ensure they work in practice."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @pytest.mark.parametrize(
        "symbol",
        [
            "dagster.asset",
            "dagster.op",
            "dagster.job",
            "dagster.resource",
            "dagster.Config",
            "dagster.DagsterInstance",
        ],
    )
    def test_check_docstrings_real_dagster_symbols(self, symbol):
        """Test checking docstrings for real Dagster symbols."""
        result = self.runner.invoke(main, ["check", "docstrings", "--symbol", symbol])

        # Should complete successfully (exit code 0 or 1 for validation errors)
        assert result.exit_code in [0, 1]

        # Should either validate the symbol or show it's excluded
        assert (
            f"Validating docstring for: {symbol}" in result.output
            or f"Symbol '{symbol}' is in the exclude list" in result.output
        )

        # Should show some result (valid or invalid or excluded)
        assert (
            "✓" in result.output
            or "✗" in result.output
            or "ERROR" in result.output
            or "WARNING" in result.output
            or "excluded" in result.output
        )

    def test_check_docstrings_dagster_package(self):
        """Test checking docstrings for the main dagster package."""
        result = self.runner.invoke(main, ["check", "docstrings", "--package", "dagster"])

        # Should complete (may have validation errors but should not crash)
        assert result.exit_code in [0, 1]
        assert "Validating" in result.output
        assert "public symbols in dagster" in result.output
        assert "Summary:" in result.output

    @pytest.mark.parametrize(
        "package",
        [
            "dagster._core.definitions",
            "dagster._core.types",
        ],
    )
    def test_check_docstrings_smaller_packages(self, package):
        """Test checking docstrings for smaller packages."""
        result = self.runner.invoke(main, ["check", "docstrings", "--package", package])

        # Should complete (may have validation errors but should not crash)
        assert result.exit_code in [0, 1]
        assert "Validating" in result.output
        assert f"public symbols in {package}" in result.output
        assert "Summary:" in result.output

    def test_ls_symbols_dagster_package(self):
        """Test listing symbols for the main dagster package."""
        result = self.runner.invoke(main, ["ls", "symbols", "--package", "dagster"])

        # Should complete successfully
        assert result.exit_code == 0

        # Should have some output (at least one symbol)
        lines = result.output.strip().split("\n")
        assert len(lines) > 0
        assert all(line.startswith("dagster") for line in lines if line.strip())

        # Should contain some @public-decorated dagster symbols
        output = result.output
        assert "dagster.Component" in output
        assert "dagster.ComponentLoadContext" in output
        assert "dagster.definitions" in output

    @pytest.mark.parametrize(
        "package",
        [
            "dagster._core.definitions",
            "dagster._core.types",
        ],
    )
    def test_ls_symbols_other_packages(self, package):
        """Test listing symbols for other packages."""
        result = self.runner.invoke(main, ["ls", "symbols", "--package", package])

        # Should complete successfully
        assert result.exit_code == 0

        # Output may be empty for packages with no @public symbols, which is valid
        lines = [line for line in result.output.strip().split("\n") if line.strip()]
        if len(lines) > 0:
            assert all(line.startswith(package) for line in lines)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_nonexistent_symbol_error_handling(self):
        """Test error handling for nonexistent symbols."""
        result = self.runner.invoke(
            main, ["check", "docstrings", "--symbol", "completely.nonexistent.symbol"]
        )

        assert result.exit_code == 1
        assert "Error:" in result.output or "ERRORS:" in result.output or "✗" in result.output

    def test_nonexistent_package_error_handling(self):
        """Test error handling for nonexistent packages."""
        result = self.runner.invoke(
            main, ["ls", "symbols", "--package", "completely.nonexistent.package"]
        )

        assert result.exit_code == 1
        assert "Error: Could not import package" in result.output

    def test_malformed_symbol_error_handling(self):
        """Test error handling for malformed symbol names."""
        result = self.runner.invoke(main, ["check", "docstrings", "--symbol", ""])

        assert result.exit_code == 1
        assert "Error:" in result.output
