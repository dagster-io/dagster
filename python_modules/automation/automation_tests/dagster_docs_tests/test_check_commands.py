"""Tests for dagster-docs check commands."""

from pathlib import Path
from unittest.mock import patch

import pytest
from automation.dagster_docs.commands.check import check
from click.testing import CliRunner


class TestCheckDocstringsCommands:
    """Test suite for check docstrings commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_check_docstrings_symbol_dagster_asset(self):
        """Test validating dagster.asset symbol docstring."""
        result = self.runner.invoke(check, ["docstrings", "--symbol", "dagster.asset"])

        # Should complete successfully (dagster.asset should have good docstring)
        assert result.exit_code == 0
        assert "Validating docstring for: dagster.asset" in result.output
        assert "✓" in result.output  # Success indicator

    def test_check_docstrings_symbol_dagster_op(self):
        """Test validating dagster.op symbol docstring."""
        result = self.runner.invoke(check, ["docstrings", "--symbol", "dagster.op"])

        # Should complete successfully
        assert result.exit_code == 0
        assert "Validating docstring for: dagster.op" in result.output

    def test_check_docstrings_symbol_dagster_job(self):
        """Test validating dagster.job symbol docstring."""
        result = self.runner.invoke(check, ["docstrings", "--symbol", "dagster.job"])

        # Should complete successfully
        assert result.exit_code == 0
        assert "Validating docstring for: dagster.job" in result.output

    def test_check_docstrings_symbol_automation_validator(self):
        """Test validating automation docstring validator symbol."""
        result = self.runner.invoke(
            check,
            ["docstrings", "--symbol", "automation.dagster_docs.validator.SymbolImporter"],
        )

        # Should complete successfully
        assert result.exit_code == 0
        assert (
            "Validating docstring for: automation.dagster_docs.validator.SymbolImporter"
            in result.output
        )

    def test_check_docstrings_symbol_nonexistent(self):
        """Test validating nonexistent symbol should fail."""
        result = self.runner.invoke(check, ["docstrings", "--symbol", "nonexistent.symbol"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error:" in result.output or "ERRORS:" in result.output or "✗" in result.output

    def test_check_docstrings_package_automation(self):
        """Test validating all docstrings in automation.dagster_docs package."""
        result = self.runner.invoke(check, ["docstrings", "--package", "automation.dagster_docs"])

        # Should complete successfully
        assert result.exit_code == 0
        assert "Validating" in result.output
        assert "public symbols in automation.dagster_docs" in result.output
        assert "Summary:" in result.output

    def test_check_docstrings_package_dagster_subset(self):
        """Test validating docstrings in a small dagster subpackage."""
        # Use a smaller package to avoid long test times
        result = self.runner.invoke(check, ["docstrings", "--package", "dagster._core.errors"])

        # Should complete (may have warnings/errors but should not crash)
        assert result.exit_code in [0, 1]  # 0 for success, 1 for validation errors
        assert "Validating" in result.output
        assert "Summary:" in result.output

    def test_check_docstrings_package_nonexistent(self):
        """Test validating nonexistent package should fail."""
        result = self.runner.invoke(check, ["docstrings", "--package", "nonexistent.package"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: Could not import package" in result.output

    @patch("automation.dagster_docs.commands.check.git_changed_files")
    @patch("automation.dagster_docs.commands.check._find_git_root")
    def test_check_docstrings_changed_no_files(self, mock_find_git_root, mock_git_changed_files):
        """Test validating changed files when no files are changed."""
        # Mock git root and no changed files
        mock_find_git_root.return_value = Path("/fake/git/root")
        mock_git_changed_files.return_value = []

        result = self.runner.invoke(check, ["docstrings", "--changed"])

        # Should complete successfully with no files message
        assert result.exit_code == 0
        assert "No changed Python files found" in result.output

    @patch("automation.dagster_docs.commands.check._find_git_root")
    def test_check_docstrings_changed_no_git_repo(self, mock_find_git_root):
        """Test validating changed files when not in git repo."""
        # Mock no git root found
        mock_find_git_root.return_value = None

        result = self.runner.invoke(check, ["docstrings", "--changed"])

        # Should fail with exit code 2 (special code for no git repo)
        assert result.exit_code == 2
        assert "Error: Not in a git repository" in result.output

    def test_check_docstrings_no_options_fails(self):
        """Test that check docstrings without options fails."""
        result = self.runner.invoke(check, ["docstrings"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert (
            "Error: Exactly one of --changed, --symbol, --all, or --package must be provided"
            in result.output
        )

    def test_check_docstrings_multiple_options_fails(self):
        """Test that check docstrings with multiple options fails."""
        result = self.runner.invoke(
            check, ["docstrings", "--symbol", "dagster.asset", "--package", "dagster"]
        )

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert (
            "Error: Exactly one of --changed, --symbol, --all, or --package must be provided"
            in result.output
        )

    def test_check_docstrings_all_not_implemented(self):
        """Test that check docstrings --all raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as excinfo:
            self.runner.invoke(check, ["docstrings", "--all"], catch_exceptions=False)

        assert "Global docstring checking functionality not yet implemented" in str(excinfo.value)

    def test_check_help_command(self):
        """Test that check help works."""
        result = self.runner.invoke(check, ["--help"])

        assert result.exit_code == 0
        assert "Check documentation aspects" in result.output
        assert "docstrings" in result.output


class TestCheckOtherCommands:
    """Test suite for other check commands that are not yet implemented."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_check_rst_symbols_runs(self):
        """Test that check rst-symbols runs without NotImplementedError."""
        result = self.runner.invoke(check, ["rst-symbols", "--all"])

        # Should not raise NotImplementedError and should exit cleanly
        assert result.exit_code in [0, 1]  # Can succeed or fail validation but shouldn't crash
        assert "RST symbol checking functionality not yet implemented" not in result.output

    def test_check_rst_symbols_no_options_fails(self):
        """Test that check rst-symbols without options fails."""
        result = self.runner.invoke(check, ["rst-symbols"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: One of --all or --package must be provided" in result.output

    def test_check_public_symbols_runs(self):
        """Test that check public-symbols runs without NotImplementedError."""
        result = self.runner.invoke(check, ["public-symbols", "--all"])

        # Should not raise NotImplementedError and should exit cleanly
        assert result.exit_code in [0, 1]  # Can succeed or fail validation but shouldn't crash
        assert "Public symbol checking functionality not yet implemented" not in result.output

    def test_check_public_symbols_no_options_fails(self):
        """Test that check public-symbols without options fails."""
        result = self.runner.invoke(check, ["public-symbols"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: One of --all or --package must be provided" in result.output

    def test_check_exports_runs(self):
        """Test that check exports runs without NotImplementedError."""
        result = self.runner.invoke(check, ["exports", "--all"])

        # Should not raise NotImplementedError and should exit cleanly
        assert result.exit_code in [0, 1]  # Can succeed or fail validation but shouldn't crash
        assert "Export checking functionality not yet implemented" not in result.output

    def test_check_exports_no_options_fails(self):
        """Test that check exports without options fails."""
        result = self.runner.invoke(check, ["exports"])

        # Should fail with exit code 1
        assert result.exit_code == 1
        assert "Error: One of --all or --package must be provided" in result.output
