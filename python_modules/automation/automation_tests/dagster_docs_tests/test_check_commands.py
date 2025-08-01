"""Tests for dagster-docs check commands."""

from pathlib import Path
from unittest.mock import patch

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

    def test_check_docstrings_all_runs_successfully(self):
        """Test that check docstrings --all executes without crashing."""
        result = self.runner.invoke(check, ["docstrings", "--all"])

        # Should complete (may have warnings/errors but should not crash)
        assert result.exit_code in [0, 1]  # 0 for success, 1 for validation errors
        assert "Validating docstrings across" in result.output
        assert "public Dagster packages" in result.output
        assert "Overall Summary:" in result.output

    def test_check_docstrings_all_shows_summary_statistics(self):
        """Test that --all shows package count and symbol statistics."""
        result = self.runner.invoke(check, ["docstrings", "--all"])

        # Should show statistics about packages and symbols processed
        assert result.exit_code in [0, 1]
        assert "symbols processed across" in result.output
        assert "packages" in result.output
        assert "Total:" in result.output
        # Should show counts for errors and warnings
        assert "errors," in result.output
        assert "warnings" in result.output

    def test_check_docstrings_all_respects_exclude_lists_by_default(self):
        """Test that exclude lists are applied by default in --all mode."""
        result = self.runner.invoke(check, ["docstrings", "--all"])

        # Should complete and may show exclusion information
        assert result.exit_code in [0, 1]
        # If exclusions exist, should mention them
        # Note: We can't assert specific exclusion counts as they may change,
        # but we can check the format is correct
        if "excluded from validation" in result.output:
            assert "symbols excluded from validation" in result.output

    def test_check_docstrings_all_handles_import_errors_gracefully(self):
        """Test graceful handling when some packages fail to import."""
        result = self.runner.invoke(check, ["docstrings", "--all"])

        # Should complete successfully even if some packages fail to import
        assert result.exit_code in [0, 1]
        # May show warnings about import failures, but should continue
        if "Warning: Could not import package" in result.output:
            # Should still show overall summary despite import failures
            assert "Overall Summary:" in result.output

    def test_check_help_command(self):
        """Test that check help works."""
        result = self.runner.invoke(check, ["--help"])

        assert result.exit_code == 0
        assert "Check documentation aspects" in result.output
        assert "docstrings" in result.output


class TestIgnoreExcludeListsFlag:
    """Test suite for --ignore-exclude-lists flag functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_ignore_exclude_lists_flag_with_symbol_excluded_symbol(self):
        """Test --ignore-exclude-lists with --symbol on a known excluded symbol."""
        # Test with a symbol we know is in EXCLUDE_MISSING_DOCSTRINGS
        result_normal = self.runner.invoke(check, ["docstrings", "--symbol", "dagster.BoolSource"])
        result_ignore = self.runner.invoke(
            check, ["docstrings", "--symbol", "dagster.BoolSource", "--ignore-exclude-lists"]
        )

        # Normal mode should skip the excluded symbol
        assert result_normal.exit_code == 0
        assert (
            "Symbol 'dagster.BoolSource' is in the exclude list - skipping validation"
            in result_normal.output
        )
        assert "✓ Symbol excluded from validation" in result_normal.output

        # Ignore mode should actually validate the symbol
        assert result_ignore.exit_code in [0, 1]  # May pass or fail validation
        assert "Validating docstring for: dagster.BoolSource" in result_ignore.output
        # Should not show exclusion message
        assert "Symbol 'dagster.BoolSource' is in the exclude list" not in result_ignore.output

    def test_ignore_exclude_lists_flag_with_symbol_non_excluded_symbol(self):
        """Test --ignore-exclude-lists with --symbol on a non-excluded symbol."""
        # Test with a symbol that should have good docstrings
        result_normal = self.runner.invoke(check, ["docstrings", "--symbol", "dagster.asset"])
        result_ignore = self.runner.invoke(
            check, ["docstrings", "--symbol", "dagster.asset", "--ignore-exclude-lists"]
        )

        # Both should behave the same for non-excluded symbols
        assert result_normal.exit_code == 0
        assert result_ignore.exit_code == 0
        assert "Validating docstring for: dagster.asset" in result_normal.output
        assert "Validating docstring for: dagster.asset" in result_ignore.output

    def test_ignore_exclude_lists_flag_with_package_shows_more_issues(self):
        """Test --ignore-exclude-lists with --package shows more validation issues."""
        # Use a small package that likely has excluded symbols
        result_normal = self.runner.invoke(
            check, ["docstrings", "--package", "dagster._core.errors"]
        )
        result_ignore = self.runner.invoke(
            check, ["docstrings", "--package", "dagster._core.errors", "--ignore-exclude-lists"]
        )

        # Both should complete
        assert result_normal.exit_code in [0, 1]
        assert result_ignore.exit_code in [0, 1]

        # Normal mode may show exclusion counts
        if "symbols excluded from validation" in result_normal.output:
            # Ignore mode should not show exclusion counts
            assert "symbols excluded from validation" not in result_ignore.output

    def test_ignore_exclude_lists_flag_with_all_shows_more_issues(self):
        """Test --ignore-exclude-lists with --all shows more validation issues."""
        result_normal = self.runner.invoke(check, ["docstrings", "--all"])
        result_ignore = self.runner.invoke(check, ["docstrings", "--all", "--ignore-exclude-lists"])

        # Both should complete
        assert result_normal.exit_code in [0, 1]
        assert result_ignore.exit_code in [0, 1]

        # Both should show overall summary
        assert "Overall Summary:" in result_normal.output
        assert "Overall Summary:" in result_ignore.output

        # Normal mode should show exclusion information if excludes exist
        normal_has_exclusions = "symbols excluded from validation" in result_normal.output
        # Ignore mode should not show exclusion information
        assert "symbols excluded from validation" not in result_ignore.output

        # If there were exclusions in normal mode, ignore mode should process more symbols
        if normal_has_exclusions:
            # Extract symbol counts (this is a bit fragile but useful for validation)
            import re

            normal_match = re.search(r"(\d+) symbols processed", result_normal.output)
            ignore_match = re.search(r"(\d+) symbols processed", result_ignore.output)

            if normal_match and ignore_match:
                normal_count = int(normal_match.group(1))
                ignore_count = int(ignore_match.group(1))
                # Ignore mode should process at least as many symbols as normal mode
                assert ignore_count >= normal_count

    def test_ignore_exclude_lists_flag_consistency_across_modes(self):
        """Test that --ignore-exclude-lists behaves consistently across different modes."""
        # Test a known excluded symbol in both single-symbol and package mode
        symbol_result = self.runner.invoke(
            check, ["docstrings", "--symbol", "dagster.BoolSource", "--ignore-exclude-lists"]
        )

        # Find which package contains dagster.BoolSource and test that package
        package_result = self.runner.invoke(
            check, ["docstrings", "--package", "dagster", "--ignore-exclude-lists"]
        )

        # Both should complete
        assert symbol_result.exit_code in [0, 1]
        assert package_result.exit_code in [0, 1]

        # Neither should show exclusion messages
        assert "is in the exclude list" not in symbol_result.output
        assert "excluded from validation" not in package_result.output

    def test_ignore_exclude_lists_flag_help_text(self):
        """Test that --ignore-exclude-lists flag appears in help text."""
        result = self.runner.invoke(check, ["docstrings", "--help"])

        assert result.exit_code == 0
        assert "--ignore-exclude-lists" in result.output
        assert "Ignore exclude lists and show all docstring issues" in result.output


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
