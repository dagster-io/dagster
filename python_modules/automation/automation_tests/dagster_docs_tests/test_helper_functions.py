"""Tests for helper functions in docs CLI commands."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from automation.dagster_docs.commands.check import (
    _find_git_root,
    _validate_changed_files,
    _validate_package_symbols,
    _validate_single_symbol,
)
from automation.dagster_docs.commands.ls import _list_package_symbols
from automation.dagster_docs.commands.watch import _resolve_symbol_file_path


class TestCheckHelperFunctions:
    """Test helper functions from check commands."""

    def test_validate_single_symbol_success(self):
        """Test _validate_single_symbol with a valid symbol."""
        # Test with automation symbol that should be valid
        result = _validate_single_symbol("automation.dagster_docs.validator.SymbolImporter")

        # Should return 0 for success
        assert result == 0

    def test_validate_single_symbol_with_invalid_symbol(self):
        """Test _validate_single_symbol with invalid symbol."""
        # Should return non-zero exit code for nonexistent symbol (not raise exception)
        # The function handles the exception internally and returns an exit code
        result = _validate_single_symbol("nonexistent.symbol")
        assert result == 1  # Should return 1 for failure

    def test_validate_package_symbols_success(self):
        """Test _validate_package_symbols with a valid package."""
        # Test with automation package
        result = _validate_package_symbols("automation.dagster_docs")

        # Should return 0 or 1 (success or validation errors, but not crash)
        assert result in [0, 1]

    def test_validate_package_symbols_nonexistent_package(self):
        """Test _validate_package_symbols with nonexistent package."""
        # Should raise ImportError for nonexistent package
        with pytest.raises(ImportError):
            _validate_package_symbols("nonexistent.package")

    def test_find_git_root_current_repo(self):
        """Test _find_git_root in current repository (which should be a git repo)."""
        result = _find_git_root()

        # Should return a Path object since we're in a git repo
        assert result is not None
        assert isinstance(result, Path)
        assert (result / ".git").exists()

    @patch("automation.dagster_docs.commands.check.Path.cwd")
    def test_find_git_root_not_found(self, mock_cwd):
        """Test _find_git_root when not in a git repository."""
        # Create a mock path that doesn't have .git and is at filesystem root
        mock_root = Mock(spec=Path)
        mock_root.parent = mock_root  # Simulate filesystem root

        # Configure the __truediv__ method to return a mock .git directory
        mock_git_dir = Mock()
        mock_git_dir.exists.return_value = False
        mock_root.__truediv__ = Mock(return_value=mock_git_dir)

        mock_cwd.return_value = mock_root

        result = _find_git_root()

        # Should return None when no git repo found
        assert result is None

    @patch("automation.dagster_docs.commands.check._find_git_root")
    def test_validate_changed_files_no_git_repo(self, mock_find_git_root):
        """Test _validate_changed_files when not in git repo."""
        mock_find_git_root.return_value = None

        result = _validate_changed_files()

        # Should return 2 for "not in git repo" error
        assert result == 2

    @patch("automation.dagster_docs.commands.check.git_changed_files")
    @patch("automation.dagster_docs.commands.check._find_git_root")
    def test_validate_changed_files_no_changes(self, mock_find_git_root, mock_git_changed_files):
        """Test _validate_changed_files when no files are changed."""
        mock_find_git_root.return_value = Path("/fake/git/root")
        mock_git_changed_files.return_value = []

        result = _validate_changed_files()

        # Should return 0 for success when no changed files
        assert result == 0


class TestLsHelperFunctions:
    """Test helper functions from ls commands."""

    def test_list_package_symbols_success(self):
        """Test _list_package_symbols with valid package."""
        # Should not raise exception for valid package
        _list_package_symbols("automation.dagster_docs")

    def test_list_package_symbols_nonexistent_package(self):
        """Test _list_package_symbols with nonexistent package."""
        # Should raise ImportError for nonexistent package
        with pytest.raises(ImportError):
            _list_package_symbols("nonexistent.package")


class TestWatchHelperFunctions:
    """Test helper functions from watch commands."""

    def test_resolve_symbol_file_path_success(self):
        """Test _resolve_symbol_file_path with valid symbol."""
        # Test with a symbol that should resolve successfully
        result = _resolve_symbol_file_path(
            "automation.dagster_docs.validator.SymbolImporter", False
        )

        # Should return a Path object
        assert isinstance(result, Path)
        assert result.exists()

    def test_resolve_symbol_file_path_nonexistent_symbol(self):
        """Test _resolve_symbol_file_path with nonexistent symbol."""
        # Should raise exception for nonexistent symbol
        with pytest.raises(Exception):
            _resolve_symbol_file_path("nonexistent.symbol", False)

    def test_resolve_symbol_file_path_verbose_mode(self):
        """Test _resolve_symbol_file_path in verbose mode."""
        # Should work the same way in verbose mode
        result = _resolve_symbol_file_path("automation.dagster_docs.validator.SymbolImporter", True)

        assert isinstance(result, Path)
        assert result.exists()
