"""Tests for the exclude-lists audit functionality."""

from unittest.mock import Mock, patch

from automation.dagster_docs.commands.check import (
    _audit_exclude_missing_export,
    _audit_exclude_missing_public,
    _audit_exclude_missing_rst,
    check,
)
from automation.dagster_docs.public_api_validator import PublicSymbol
from click.testing import CliRunner


class TestAuditExcludeMissingPublic:
    """Test suite for _audit_exclude_missing_public function."""

    def test_audit_exclude_missing_public_all_valid(self):
        """Test audit when all EXCLUDE_MISSING_PUBLIC entries are still valid."""
        # Mock validator with no symbols having @public decorators
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = []

        with patch(
            "automation.dagster_docs.commands.check.EXCLUDE_MISSING_PUBLIC",
            {"symbol.one", "symbol.two"},
        ):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_public(mock_validator)

        assert result == 0
        mock_echo.assert_called_with(
            "✓ All entries in EXCLUDE_MISSING_PUBLIC are still valid (symbols still missing @public decorators)"
        )

    def test_audit_exclude_missing_public_some_have_public(self):
        """Test audit when some EXCLUDE_MISSING_PUBLIC entries now have @public decorators."""
        # Mock validator with some symbols having @public decorators
        mock_symbols = [
            PublicSymbol(
                module_path="test.module",
                symbol_name="one",
                symbol_type="function",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
            PublicSymbol(
                module_path="test.module",
                symbol_name="three",
                symbol_type="class",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
        ]
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = mock_symbols

        with patch(
            "automation.dagster_docs.commands.check.EXCLUDE_MISSING_PUBLIC",
            {"test.module.one", "test.module.two", "test.module.three"},
        ):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_public(mock_validator)

        assert result == 1
        # Should report the symbols that can be removed
        call_args = [str(call.args[0]) for call in mock_echo.call_args_list if call.args]
        output_text = "\n".join(call_args)
        assert "test.module.one" in output_text
        assert "test.module.three" in output_text
        assert "test.module.two" not in output_text  # This one doesn't have @public


class TestAuditExcludeMissingRst:
    """Test suite for _audit_exclude_missing_rst function."""

    def test_audit_exclude_missing_rst_all_valid(self):
        """Test audit when all EXCLUDE_MISSING_RST entries are still valid."""
        # Mock validator with no symbols having RST documentation
        mock_validator = Mock()
        mock_validator.find_rst_documented_symbols.return_value = []

        with patch(
            "automation.dagster_docs.commands.check.EXCLUDE_MISSING_RST",
            {"symbol.one", "symbol.two"},
        ):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_rst(mock_validator)

        assert result == 0
        mock_echo.assert_called_with(
            "✓ All entries in EXCLUDE_MISSING_RST are still valid (symbols still missing RST documentation)"
        )

    def test_audit_exclude_missing_rst_some_have_rst(self):
        """Test audit when some EXCLUDE_MISSING_RST entries now have RST documentation."""
        # Mock validator with some symbols having RST documentation
        mock_symbols = [
            PublicSymbol(
                module_path="test.module",
                symbol_name="one",
                symbol_type="function",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
            PublicSymbol(
                module_path="test.module",
                symbol_name="three",
                symbol_type="class",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
        ]
        mock_validator = Mock()
        mock_validator.find_rst_documented_symbols.return_value = mock_symbols

        with patch(
            "automation.dagster_docs.commands.check.EXCLUDE_MISSING_RST",
            {"test.module.one", "test.module.two", "test.module.three"},
        ):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_rst(mock_validator)

        assert result == 1
        # Should report the symbols that can be removed
        call_args = [str(call.args[0]) for call in mock_echo.call_args_list if call.args]
        output_text = "\n".join(call_args)
        assert "test.module.one" in output_text
        assert "test.module.three" in output_text
        assert "test.module.two" not in output_text  # This one doesn't have RST


class TestAuditExcludeMissingExport:
    """Test suite for _audit_exclude_missing_export function."""

    def test_audit_exclude_missing_export_all_valid(self):
        """Test audit when all EXCLUDE_MISSING_EXPORT entries are still valid."""
        # Mock validator with symbols that are not exported
        mock_symbols = [
            PublicSymbol(
                module_path="test.module",
                symbol_name="one",
                symbol_type="function",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
            PublicSymbol(
                module_path="test.module",
                symbol_name="two",
                symbol_type="class",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
        ]
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = mock_symbols

        with patch(
            "automation.dagster_docs.commands.check.EXCLUDE_MISSING_EXPORT",
            {"test.module.one", "test.module.two"},
        ):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_export(mock_validator)

        assert result == 0
        mock_echo.assert_called_with(
            "✓ All entries in EXCLUDE_MISSING_EXPORT are still valid (symbols still not exported at top-level)"
        )

    def test_audit_exclude_missing_export_some_exported(self):
        """Test audit when some EXCLUDE_MISSING_EXPORT entries are now exported."""
        # Mock validator with some symbols that are exported
        mock_symbols = [
            PublicSymbol(
                module_path="test.module",
                symbol_name="one",
                symbol_type="function",
                is_exported=True,
                source_file="/path/to/test/module.py",
            ),
            PublicSymbol(
                module_path="test.module",
                symbol_name="two",
                symbol_type="class",
                is_exported=False,
                source_file="/path/to/test/module.py",
            ),
            PublicSymbol(
                module_path="test.module",
                symbol_name="three",
                symbol_type="function",
                is_exported=True,
                source_file="/path/to/test/module.py",
            ),
        ]
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = mock_symbols

        with patch(
            "automation.dagster_docs.commands.check.EXCLUDE_MISSING_EXPORT",
            {"test.module.one", "test.module.two", "test.module.three"},
        ):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_export(mock_validator)

        assert result == 1
        # Should report the symbols that can be removed (the exported ones)
        call_args = [str(call.args[0]) for call in mock_echo.call_args_list if call.args]
        output_text = "\n".join(call_args)
        assert "test.module.one" in output_text
        assert "test.module.three" in output_text
        assert "test.module.two" not in output_text  # This one is not exported

    def test_audit_exclude_missing_export_empty_exclude_list(self):
        """Test audit when EXCLUDE_MISSING_EXPORT is empty."""
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = []

        with patch("automation.dagster_docs.commands.check.EXCLUDE_MISSING_EXPORT", set()):
            with patch("automation.dagster_docs.commands.check.click.echo") as mock_echo:
                result = _audit_exclude_missing_export(mock_validator)

        assert result == 0
        mock_echo.assert_called_with(
            "✓ All entries in EXCLUDE_MISSING_EXPORT are still valid (symbols still not exported at top-level)"
        )


class TestAuditFunctionsCallValidator:
    """Test that audit functions call the validator with correct parameters."""

    def test_audit_missing_public_calls_validator_correctly(self):
        """Test that _audit_exclude_missing_public calls validator with correct parameters."""
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = []

        with patch("automation.dagster_docs.commands.check.EXCLUDE_MISSING_PUBLIC", set()):
            with patch(
                "automation.dagster_docs.commands.check.EXCLUDE_MODULES_FROM_PUBLIC_SCAN",
                {"excluded.module"},
            ):
                _audit_exclude_missing_public(mock_validator)

        mock_validator.find_public_symbols.assert_called_once_with(
            exclude_modules={"excluded.module"}
        )

    def test_audit_missing_rst_calls_validator_correctly(self):
        """Test that _audit_exclude_missing_rst calls validator with correct parameters."""
        mock_validator = Mock()
        mock_validator.find_rst_documented_symbols.return_value = []

        with patch("automation.dagster_docs.commands.check.EXCLUDE_MISSING_RST", set()):
            with patch(
                "automation.dagster_docs.commands.check.EXCLUDE_RST_FILES", {"excluded.rst"}
            ):
                _audit_exclude_missing_rst(mock_validator)

        mock_validator.find_rst_documented_symbols.assert_called_once_with(
            exclude_files={"excluded.rst"}
        )

    def test_audit_missing_export_calls_validator_correctly(self):
        """Test that _audit_exclude_missing_export calls validator with correct parameters."""
        mock_validator = Mock()
        mock_validator.find_public_symbols.return_value = []

        with patch("automation.dagster_docs.commands.check.EXCLUDE_MISSING_EXPORT", set()):
            with patch(
                "automation.dagster_docs.commands.check.EXCLUDE_MODULES_FROM_PUBLIC_SCAN",
                {"excluded.module"},
            ):
                _audit_exclude_missing_export(mock_validator)

        mock_validator.find_public_symbols.assert_called_once_with(
            exclude_modules={"excluded.module"}
        )


class TestCheckExcludeListsCommand:
    """Test suite for the exclude-lists CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_exclude_lists_no_options_fails(self):
        """Test that exclude-lists command without options fails."""
        result = self.runner.invoke(check, ["exclude-lists"])

        assert result.exit_code == 1
        assert "Error: Must specify at least one exclude list to check" in result.output

    def test_exclude_lists_missing_public_flag(self):
        """Test exclude-lists command with --missing-public flag."""
        result = self.runner.invoke(check, ["exclude-lists", "--missing-public"])

        # Should complete without error (may or may not find issues)
        assert result.exit_code in [0, 1]
        assert "EXCLUDE_MISSING_PUBLIC" in result.output

    def test_exclude_lists_missing_rst_flag(self):
        """Test exclude-lists command with --missing-rst flag."""
        result = self.runner.invoke(check, ["exclude-lists", "--missing-rst"])

        # Should complete without error (may or may not find issues)
        assert result.exit_code in [0, 1]
        assert "EXCLUDE_MISSING_RST" in result.output

    def test_exclude_lists_missing_export_flag(self):
        """Test exclude-lists command with --missing-export flag."""
        result = self.runner.invoke(check, ["exclude-lists", "--missing-export"])

        # Should complete without error (may or may not find issues)
        assert result.exit_code in [0, 1]
        assert "EXCLUDE_MISSING_EXPORT" in result.output

    def test_exclude_lists_all_flags_together(self):
        """Test exclude-lists command with all flags together."""
        result = self.runner.invoke(
            check, ["exclude-lists", "--missing-public", "--missing-rst", "--missing-export"]
        )

        # Should complete without error
        assert result.exit_code in [0, 1]
        # Should contain output from all three audits
        assert "EXCLUDE_MISSING_PUBLIC" in result.output
        assert "EXCLUDE_MISSING_RST" in result.output
        assert "EXCLUDE_MISSING_EXPORT" in result.output

    def test_exclude_lists_multiple_flags_with_separators(self):
        """Test that multiple flags show separator lines between outputs."""
        result = self.runner.invoke(check, ["exclude-lists", "--missing-public", "--missing-rst"])

        # Should complete without error
        assert result.exit_code in [0, 1]
        # Should have separator between outputs if both ran
        if "EXCLUDE_MISSING_PUBLIC" in result.output and "EXCLUDE_MISSING_RST" in result.output:
            assert "=" * 80 in result.output

    def test_exclude_lists_help_command(self):
        """Test that exclude-lists help works."""
        result = self.runner.invoke(check, ["exclude-lists", "--help"])

        assert result.exit_code == 0
        assert "Audit exclude lists to ensure entries are still necessary" in result.output
        assert "--missing-public" in result.output
        assert "--missing-rst" in result.output
        assert "--missing-export" in result.output

    @patch("automation.dagster_docs.commands.check._find_dagster_root")
    def test_exclude_lists_no_dagster_root(self, mock_find_dagster_root):
        """Test exclude-lists command when not in dagster repository."""
        mock_find_dagster_root.return_value = None

        result = self.runner.invoke(check, ["exclude-lists", "--missing-public"])

        assert result.exit_code == 1
        assert "Error: Could not find dagster repository root" in result.output


class TestCheckCommandsWithExcludeLists:
    """Test suite to verify commands respect exclude lists and return clean results."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_check_rst_symbols_all_with_exclude_lists(self):
        """Test that check rst-symbols --all returns clean results with exclude lists."""
        result = self.runner.invoke(check, ["rst-symbols", "--all"])

        # With exclude lists properly applied, should have no issues
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "✓" in result.output
        assert "All RST documented symbols have @public decorators" in result.output

    def test_check_public_symbols_all_with_exclude_lists(self):
        """Test that check public-symbols --all returns clean results with exclude lists."""
        result = self.runner.invoke(check, ["public-symbols", "--all"])

        # With exclude lists properly applied, should have no issues
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "✓" in result.output
        assert "All @public symbols are documented in RST and exported top-level" in result.output

    def test_check_exports_all_with_exclude_lists(self):
        """Test that check exports --all returns clean results with exclude lists."""
        result = self.runner.invoke(check, ["exports", "--all"])

        # With exclude lists properly applied, should have no issues
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "✓" in result.output
        assert "All exports are properly documented and decorated" in result.output
