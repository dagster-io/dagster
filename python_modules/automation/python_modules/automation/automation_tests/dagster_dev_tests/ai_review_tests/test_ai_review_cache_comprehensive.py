"""Comprehensive tests for ai-review-cache command targeting 85% coverage."""

import json
import time
from unittest.mock import Mock, patch

from click.testing import CliRunner


class TestAiReviewCacheComprehensive:
    """Comprehensive test coverage for ai-review-cache command."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        assert ai_review_cache is not None
        assert ai_review_cache.name == "ai-review-cache"
        assert callable(ai_review_cache)

    def test_help_command(self):
        """Test that help command works and contains expected content."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-cache" in result.output
        assert "--action" in result.output
        assert "--format" in result.output
        assert "status" in result.output
        assert "clear" in result.output
        assert "json" in result.output
        assert "human" in result.output

    def test_default_parameters(self):
        """Test command with default parameters (action=status, format=human)."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": False,
                "size_bytes": 0,
                "entries": 0,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, [])

            assert result.exit_code == 0
            assert "📊 AI Review Cache Status" in result.output
            assert "No cache found" in result.output

    def test_status_action_no_cache_human_format(self):
        """Test status action when no cache exists with human format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": False,
                "size_bytes": 0,
                "entries": 0,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status", "--format", "human"])

            assert result.exit_code == 0
            assert "📊 AI Review Cache Status" in result.output
            assert "No cache found" in result.output

    def test_status_action_no_cache_json_format(self):
        """Test status action when no cache exists with JSON format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            status_data = {"exists": False, "size_bytes": 0, "entries": 0}
            mock_instance.get_cache_status.return_value = status_data
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status", "--format", "json"])

            assert result.exit_code == 0

            # Verify JSON output
            output_json = json.loads(result.output.strip())
            assert output_json == status_data

    def test_status_action_with_valid_cache_human_format(self):
        """Test status action when cache exists and is valid with human format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 1024,
                "entries": 1,
                "last_analysis": 1640995200.0,  # 2022-01-01 00:00:00 UTC
                "cached_commit": "abc123def456",
                "cached_branch": "main",
                "is_valid": True,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "📊 AI Review Cache Status" in result.output
            assert "Cache size: 1,024 bytes" in result.output
            assert "Entries: 1" in result.output
            assert "Last analysis:" in result.output
            assert "Cached commit: abc123def456" in result.output
            assert "Cached branch: main" in result.output
            assert "✅ Yes" in result.output

    def test_status_action_with_stale_cache_human_format(self):
        """Test status action when cache exists but is stale with human format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 2048,
                "entries": 1,
                "last_analysis": 1640995200.0,
                "cached_commit": "old123commit",
                "cached_branch": "feature",
                "is_valid": False,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "Cache size: 2,048 bytes" in result.output
            assert "❌ No (stale)" in result.output

    def test_status_action_with_corrupted_cache_human_format(self):
        """Test status action when cache exists but is corrupted with human format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 512,
                "entries": 0,
                "error": "Corrupted cache file",
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "❌ Error: Corrupted cache file" in result.output

    def test_clear_action_success(self):
        """Test clear action when cache clearing succeeds."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.clear_cache.return_value = True
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "clear"])

            assert result.exit_code == 0
            assert "✅ Cache cleared successfully" in result.output
            mock_instance.clear_cache.assert_called_once()

    def test_clear_action_failure(self):
        """Test clear action when cache clearing fails."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.clear_cache.return_value = False
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "clear"])

            assert result.exit_code == 1
            assert "❌ Failed to clear cache" in result.output

    def test_git_repository_error(self):
        """Test error handling when not in a git repository."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_cache_manager.side_effect = ValueError(
                "Not in a git repository - cannot create cache"
            )

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 1
            assert "❌ Error: Must be run from within a git repository" in result.output

    def test_other_value_error(self):
        """Test error handling for other ValueError scenarios."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_cache_manager.side_effect = ValueError("Some other error")

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 1
            assert "❌ Error: Some other error" in result.output

    def test_unexpected_exception(self):
        """Test error handling for unexpected exceptions."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_cache_manager.side_effect = RuntimeError("Unexpected runtime error")

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 1
            assert "❌ Unexpected error: Unexpected runtime error" in result.output

    def test_exception_during_status_operation(self):
        """Test error handling when exception occurs during status operation."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.side_effect = RuntimeError("Status check failed")
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 1
            assert "❌ Unexpected error: Status check failed" in result.output

    def test_exception_during_clear_operation(self):
        """Test error handling when exception occurs during clear operation."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.clear_cache.side_effect = RuntimeError("Clear operation failed")
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "clear"])

            assert result.exit_code == 1
            assert "❌ Unexpected error: Clear operation failed" in result.output

    def test_invalid_action_parameter(self):
        """Test that invalid action parameter is rejected."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--action", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value for '--action'" in result.output

    def test_invalid_format_parameter(self):
        """Test that invalid format parameter is rejected."""
        from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

        runner = CliRunner()
        result = runner.invoke(ai_review_cache, ["--format", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value for '--format'" in result.output

    def test_case_insensitive_parameters(self):
        """Test that parameters are case insensitive."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": False,
                "size_bytes": 0,
                "entries": 0,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()

            # Test uppercase action
            result = runner.invoke(ai_review_cache, ["--action", "STATUS"])
            assert result.exit_code == 0

            # Test uppercase format
            result = runner.invoke(ai_review_cache, ["--format", "JSON"])
            assert result.exit_code == 0

    @patch("time.strftime")
    def test_time_formatting_in_status_display(self, mock_strftime):
        """Test that time formatting works correctly in status display."""
        mock_strftime.return_value = "2022-01-01 12:00:00"

        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 1024,
                "entries": 1,
                "last_analysis": 1640995200.0,
                "cached_commit": "abc123",
                "cached_branch": "main",
                "is_valid": True,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "Last analysis: 2022-01-01 12:00:00" in result.output
            mock_strftime.assert_called_once_with("%Y-%m-%d %H:%M:%S", time.localtime(1640995200.0))

    def test_large_cache_size_formatting(self):
        """Test formatting of large cache sizes with comma separators."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 1234567,
                "entries": 1,
                "last_analysis": 1640995200.0,
                "cached_commit": "abc123",
                "cached_branch": "main",
                "is_valid": True,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "Cache size: 1,234,567 bytes" in result.output
