"""Comprehensive test suite for ai-review commands targeting 80% coverage."""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner


class TestAiReviewCacheComprehensive:
    """Comprehensive tests for ai-review-cache targeting 85% coverage."""

    def test_status_no_cache_human_format(self):
        """Test status when no cache exists with human format."""
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
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "📊 AI Review Cache Status" in result.output
            assert "No cache found" in result.output

    def test_status_no_cache_json_format(self):
        """Test status when no cache exists with JSON format."""
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
            output_json = json.loads(result.output.strip())
            assert output_json == status_data

    def test_status_valid_cache_human_format(self):
        """Test status when cache exists and is valid."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 1024,
                "entries": 1,
                "last_analysis": 1640995200.0,
                "cached_commit": "abc123def456",
                "cached_branch": "main",
                "is_valid": True,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "Cache size: 1,024 bytes" in result.output
            assert "✅ Yes" in result.output

    def test_status_stale_cache(self):
        """Test status when cache is stale."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_instance = Mock()
            mock_instance.get_cache_status.return_value = {
                "exists": True,
                "size_bytes": 2048,
                "entries": 1,
                "last_analysis": 1640995200.0,
                "cached_commit": "old123",
                "cached_branch": "feature",
                "is_valid": False,
            }
            mock_cache_manager.return_value = mock_instance

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 0
            assert "❌ No (stale)" in result.output

    def test_status_corrupted_cache(self):
        """Test status when cache is corrupted."""
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

    def test_clear_success(self):
        """Test successful cache clearing."""
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

    def test_clear_failure(self):
        """Test failed cache clearing."""
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
        """Test error when not in git repository."""
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
        """Test other ValueError handling."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_cache_manager.side_effect = ValueError("Other error")

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 1
            assert "❌ Error: Other error" in result.output

    def test_unexpected_exception(self):
        """Test unexpected exception handling."""
        with patch(
            "automation.dagster_dev.commands.ai_review_cache.CacheManager"
        ) as mock_cache_manager:
            mock_cache_manager.side_effect = RuntimeError("Unexpected error")

            from automation.dagster_dev.commands.ai_review_cache import ai_review_cache

            runner = CliRunner()
            result = runner.invoke(ai_review_cache, ["--action", "status"])

            assert result.exit_code == 1
            assert "❌ Unexpected error: Unexpected error" in result.output

    def test_default_parameters(self):
        """Test default parameter behavior."""
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
            assert "No cache found" in result.output

    @patch("time.strftime")
    def test_time_formatting(self, mock_strftime):
        """Test time formatting in status display."""
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

    def test_large_size_formatting(self):
        """Test formatting of large cache sizes."""
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


class TestAiReviewSummarizeComprehensive:
    """Comprehensive tests for ai-review-summarize targeting 80% coverage."""

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_basic_json_output(self, mock_diff):
        """Test basic JSON output with confidence above threshold."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.8
        mock_diff.return_value = mock_summary

        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.format_summary_for_ai"
        ) as mock_format:
            mock_format.return_value = {"summary": "test"}

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--format", "json"])

            assert result.exit_code == 0
            mock_diff.assert_called_once()
            mock_format.assert_called_once()

    @patch("automation.dagster_dev.commands.ai_review_summarize.format_summary_for_ai")
    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_low_confidence_json_output(self, mock_diff, mock_format):
        """Test JSON output with low confidence warning."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.5
        mock_diff.return_value = mock_summary
        mock_format.return_value = {"summary": "test"}

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(
            ai_review_summarize, ["--confidence-threshold", "0.8", "--format", "json"]
        )

        assert result.exit_code == 0
        assert "⚠️  Summary confidence" in result.output
        mock_format.assert_called_once()

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_low_confidence_human_output(self, mock_diff):
        """Test human output with low confidence warning."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.4
        mock_summary.change_category = Mock()
        mock_summary.change_category.value = "bugfix"
        mock_summary.files_changed = 2
        mock_summary.additions = 10
        mock_summary.deletions = 5
        mock_summary.functions = []
        mock_summary.classes = []
        mock_summary.imports = []
        mock_summary.api_changes = []
        mock_summary.key_implementation_details = ""
        mock_summary.needs_detailed_review = False
        mock_diff.return_value = mock_summary

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(
            ai_review_summarize, ["--format", "human", "--confidence-threshold", "0.7"]
        )

        assert result.exit_code == 0
        assert "🔍 Analyzing changes in range: master..HEAD" in result.output
        assert "⚠️  Summary confidence" in result.output
        assert "📋 Change Summary" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_human_format_complete_display(self, mock_diff):
        """Test human format with complete summary display."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.9
        mock_summary.change_category = Mock()
        mock_summary.change_category.value = "feature"
        mock_summary.files_changed = 5
        mock_summary.additions = 100
        mock_summary.deletions = 20
        mock_summary.functions = [Mock(details="add_function()"), Mock(details="modify_function()")]
        mock_summary.classes = [Mock(details="NewClass")]
        mock_summary.imports = [Mock(details="import module")]
        mock_summary.api_changes = ["Added new API endpoint"]
        mock_summary.key_implementation_details = "Key implementation details here"
        mock_summary.needs_detailed_review = False
        mock_diff.return_value = mock_summary

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "human"])

        assert result.exit_code == 0
        assert "📋 Change Summary" in result.output
        assert "Category: feature" in result.output
        assert "Scope: 5 files, +100/-20 lines" in result.output
        assert "🔧 Function Changes:" in result.output
        assert "📦 Class Changes:" in result.output
        assert "📥 Import Changes:" in result.output
        assert "🔗 API Impact:" in result.output
        assert "💡 Key Implementation Details:" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_needs_detailed_review_warning(self, mock_diff):
        """Test detailed review warning display."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.9
        mock_summary.change_category = Mock()
        mock_summary.change_category.value = "refactor"
        mock_summary.files_changed = 50
        mock_summary.additions = 1000
        mock_summary.deletions = 500
        mock_summary.functions = []
        mock_summary.classes = []
        mock_summary.imports = []
        mock_summary.api_changes = []
        mock_summary.key_implementation_details = ""
        mock_summary.needs_detailed_review = True
        mock_diff.return_value = mock_summary

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "human"])

        assert result.exit_code == 0
        assert "⚠️  Recommendation: Large change - consider full diff review" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_value_error_handling(self, mock_diff):
        """Test ValueError handling."""
        mock_diff.side_effect = ValueError("Invalid diff range")

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, [])

        assert result.exit_code == 1
        assert "❌ Error analyzing diff: Invalid diff range" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_unexpected_exception_handling(self, mock_diff):
        """Test unexpected exception handling."""
        mock_diff.side_effect = RuntimeError("Unexpected error")

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, [])

        assert result.exit_code == 1
        assert "❌ Unexpected error: Unexpected error" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_custom_diff_range(self, mock_diff):
        """Test custom diff range parameter."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.8
        mock_diff.return_value = mock_summary

        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.format_summary_for_ai"
        ) as mock_format:
            mock_format.return_value = {"summary": "test"}

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--diff-range", "HEAD~3..HEAD"])

            assert result.exit_code == 0
            assert "🔍 Analyzing changes in range: HEAD~3..HEAD" in result.output
            mock_diff.assert_called_once_with("HEAD~3..HEAD")

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_truncated_details_display(self, mock_diff):
        """Test truncation of long implementation details."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.9
        mock_summary.change_category = Mock()
        mock_summary.change_category.value = "feature"
        mock_summary.files_changed = 1
        mock_summary.additions = 10
        mock_summary.deletions = 5
        mock_summary.functions = []
        mock_summary.classes = []
        mock_summary.imports = []
        mock_summary.api_changes = []
        # Long implementation details that should be truncated
        long_details = "\n".join([f"Detail line {i}" for i in range(15)])
        mock_summary.key_implementation_details = long_details
        mock_summary.needs_detailed_review = False
        mock_diff.return_value = mock_summary

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "human"])

        assert result.exit_code == 0
        assert "... (truncated)" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_empty_sections_not_displayed(self, mock_diff):
        """Test that empty sections are not displayed in human format."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.9
        mock_summary.change_category = Mock()
        mock_summary.change_category.value = "bugfix"
        mock_summary.files_changed = 1
        mock_summary.additions = 5
        mock_summary.deletions = 2
        # Empty lists - these sections should not be displayed
        mock_summary.functions = []
        mock_summary.classes = []
        mock_summary.imports = []
        mock_summary.api_changes = []
        mock_summary.key_implementation_details = ""
        mock_summary.needs_detailed_review = False
        mock_diff.return_value = mock_summary

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "human"])

        assert result.exit_code == 0
        assert "📋 Change Summary" in result.output
        assert "Category: bugfix" in result.output
        # These sections should not appear when empty
        assert "🔧 Function Changes:" not in result.output
        assert "📦 Class Changes:" not in result.output
        assert "📥 Import Changes:" not in result.output
        assert "🔗 API Impact:" not in result.output
        assert "💡 Key Implementation Details:" not in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_format_summary_for_ai_exception(self, mock_diff):
        """Test exception handling in format_summary_for_ai."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.8
        mock_diff.return_value = mock_summary

        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.format_summary_for_ai"
        ) as mock_format:
            mock_format.side_effect = RuntimeError("Format error")

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--format", "json"])

            assert result.exit_code == 1
            assert "❌ Unexpected error: Format error" in result.output

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_default_parameters(self, mock_diff):
        """Test command with default parameters (format=json, confidence-threshold=0.7)."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.8
        mock_diff.return_value = mock_summary

        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.format_summary_for_ai"
        ) as mock_format:
            mock_format.return_value = {"summary": "test"}

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, [])

            assert result.exit_code == 0
            assert "🔍 Analyzing changes in range: master..HEAD" in result.output
            # Should not show low confidence warning since 0.8 > 0.7 (default threshold)
            assert "⚠️  Summary confidence" not in result.output
            mock_diff.assert_called_once_with("master..HEAD")

    @patch("automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary")
    def test_multiple_function_changes(self, mock_diff):
        """Test display of multiple function changes."""
        mock_summary = Mock()
        mock_summary.summary_confidence = 0.9
        mock_summary.change_category = Mock()
        mock_summary.change_category.value = "refactor"
        mock_summary.files_changed = 3
        mock_summary.additions = 50
        mock_summary.deletions = 30
        # Multiple function changes
        mock_fn1 = Mock()
        mock_fn1.details = "Added validate_input() function"
        mock_fn2 = Mock()
        mock_fn2.details = "Modified process_data() to handle edge cases"
        mock_fn3 = Mock()
        mock_fn3.details = "Removed deprecated_function()"
        mock_summary.functions = [mock_fn1, mock_fn2, mock_fn3]
        mock_summary.classes = []
        mock_summary.imports = []
        mock_summary.api_changes = []
        mock_summary.key_implementation_details = "Improved data processing pipeline"
        mock_summary.needs_detailed_review = False
        mock_diff.return_value = mock_summary

        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "human"])

        assert result.exit_code == 0
        assert "🔧 Function Changes:" in result.output
        assert "Added validate_input() function" in result.output
        assert "Modified process_data() to handle edge cases" in result.output
        assert "Removed deprecated_function()" in result.output


class TestAiReviewAnalyzeComprehensive:
    """Comprehensive tests for ai-review-analyze targeting 75% coverage."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        assert ai_review_analyze is not None
        assert ai_review_analyze.name == "ai-review-analyze"
        assert callable(ai_review_analyze)

    def test_help_command(self):
        """Test that help command works and contains expected content."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-analyze" in result.output
        assert "--human" in result.output
        assert "--json" in result.output
        assert "--minimal" in result.output
        assert "--smart-summary" in result.output

    @patch("automation.dagster_dev.commands.ai_review_analyze.run_command")
    @patch("automation.dagster_dev.commands.ai_review_analyze.check_pr_exists")
    @patch("automation.dagster_dev.commands.ai_review_analyze.get_git_status")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_squash")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_submit")
    def test_default_json_output(
        self,
        mock_needs_submit,
        mock_needs_squash,
        mock_git_status,
        mock_pr_exists,
        mock_run_command,
    ):
        """Test default JSON output with minimal mocking."""
        # Mock responses for subprocess calls
        mock_run_command.side_effect = [
            Mock(stdout="main"),  # git branch --show-current
            Mock(stdout='[{"name": "main", "is_current": true}]'),  # gt-stack --current-only
            Mock(stdout='[{"name": "main", "is_current": true}]'),  # gt-stack
            Mock(stdout="1 file changed, 10 insertions(+), 0 deletions(-)"),  # git diff --stat
            Mock(stdout="diff content"),  # git diff
            Mock(stdout="abc123 Initial commit"),  # git log --oneline
        ]
        mock_pr_exists.return_value = "123"
        mock_git_status.return_value = "clean"
        mock_needs_squash.return_value = False
        mock_needs_submit.return_value = False

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, [])

        assert result.exit_code == 0
        # Should be valid JSON
        output_json = json.loads(result.output)
        assert "current_branch" in output_json
        assert "pr_number" in output_json
        assert "changes" in output_json
        assert "validation" in output_json

    @patch("automation.dagster_dev.commands.ai_review_analyze.run_command")
    @patch("automation.dagster_dev.commands.ai_review_analyze.check_pr_exists")
    @patch("automation.dagster_dev.commands.ai_review_analyze.get_git_status")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_squash")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_submit")
    def test_human_output_format(
        self,
        mock_needs_submit,
        mock_needs_squash,
        mock_git_status,
        mock_pr_exists,
        mock_run_command,
    ):
        """Test human-readable output format."""
        mock_run_command.side_effect = [
            Mock(stdout="feature-branch"),  # git branch --show-current
            Mock(
                stdout='[{"name": "feature-branch", "is_current": true}]'
            ),  # gt-stack --current-only
            Mock(
                stdout='[{"name": "feature-branch", "is_current": true}, {"name": "main", "is_current": false}]'
            ),  # gt-stack
            Mock(stdout="2 files changed, 25 insertions(+), 5 deletions(-)"),  # git diff --stat
            Mock(stdout="diff content with test_"),  # git diff
            Mock(stdout="def123 Add feature\nabc456 Fix bug"),  # git log --oneline
        ]
        mock_pr_exists.return_value = None  # No PR
        mock_git_status.return_value = "dirty"
        mock_needs_squash.return_value = True
        mock_needs_submit.return_value = True

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--human"])

        assert result.exit_code == 0
        assert "Current Branch: feature-branch" in result.output
        assert "Previous Branch: main" in result.output
        assert "PR Number: None" in result.output
        assert "Repository State: dirty" in result.output
        assert "Files Changed: 2" in result.output
        assert "Needs Squash: True" in result.output
        assert "Needs Submit: True" in result.output

    @patch("automation.dagster_dev.commands.ai_review_analyze.run_command")
    @patch("automation.dagster_dev.commands.ai_review_analyze.check_pr_exists")
    @patch("automation.dagster_dev.commands.ai_review_analyze.get_git_status")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_squash")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_submit")
    def test_minimal_output_flag(
        self,
        mock_needs_submit,
        mock_needs_squash,
        mock_git_status,
        mock_pr_exists,
        mock_run_command,
    ):
        """Test minimal output flag excludes full stack structure."""
        mock_run_command.side_effect = [
            Mock(stdout="feature"),  # git branch --show-current
            Mock(stdout='[{"name": "feature", "is_current": true}]'),  # gt-stack --current-only
            Mock(stdout='[{"name": "feature", "is_current": true}]'),  # gt-stack --stack
            Mock(stdout="1 file changed, 5 insertions(+)"),  # git diff --stat
            Mock(stdout="diff"),  # git diff
            Mock(stdout="abc123 commit"),  # git log --oneline
        ]
        mock_pr_exists.return_value = "456"
        mock_git_status.return_value = "clean"
        mock_needs_squash.return_value = False
        mock_needs_submit.return_value = False

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--minimal"])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        # Should have current_branch_info but not stack_structure
        assert "current_branch_info" in output_json["stack_info"]
        assert "stack_structure" not in output_json["stack_info"]

    @patch("automation.dagster_dev.commands.ai_review_analyze.run_command")
    @patch("automation.dagster_dev.commands.ai_review_analyze.check_pr_exists")
    @patch("automation.dagster_dev.commands.ai_review_analyze.get_git_status")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_squash")
    @patch("automation.dagster_dev.commands.ai_review_analyze.needs_submit")
    @patch("automation.dagster_dev.commands.ai_review_analyze.get_smart_diff_summary")
    @patch("automation.dagster_dev.commands.ai_review_analyze.format_summary_for_ai")
    def test_smart_summary_flag(
        self,
        mock_format_ai,
        mock_smart_summary,
        mock_needs_submit,
        mock_needs_squash,
        mock_git_status,
        mock_pr_exists,
        mock_run_command,
    ):
        """Test smart summary flag uses intelligent diff analysis."""
        # Setup smart summary mocks
        mock_summary = Mock()
        mock_summary.change_category.value = "new_feature"
        mock_smart_summary.return_value = mock_summary
        mock_format_ai.return_value = {"category": "new_feature"}

        mock_run_command.side_effect = [
            Mock(stdout="feature"),  # git branch --show-current
            Mock(stdout='[{"name": "feature", "is_current": true}]'),  # gt-stack --current-only
            Mock(stdout='[{"name": "feature", "is_current": true}]'),  # gt-stack
            Mock(stdout="src/new_feature.py | 20 ++++++++++++++++++++"),  # git diff --stat
            Mock(stdout="abc123 Add new feature"),  # git log --oneline
        ]
        mock_pr_exists.return_value = None
        mock_git_status.return_value = "clean"
        mock_needs_squash.return_value = False
        mock_needs_submit.return_value = False

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--smart-summary"])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert "smart_analysis" in output_json["changes"]
        assert "(new feature)" in output_json["changes"]["diff_summary"]

    @patch("automation.dagster_dev.commands.ai_review_analyze.run_command")
    def test_exception_handling(self, mock_run_command):
        """Test exception handling for command failures."""
        mock_run_command.side_effect = RuntimeError("Git command failed")

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, [])

        assert result.exit_code == 1
        assert "Error analyzing PR context" in result.output

    @patch("subprocess.run")
    def test_check_pr_exists_no_pr(self, mock_subprocess_run):
        """Test check_pr_exists when no PR exists."""
        # Simulate gh command returning exit code 1 (no PR)
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "gh")

        from automation.dagster_dev.commands.ai_review_analyze import check_pr_exists

        result = check_pr_exists()
        assert result is None

    @patch("subprocess.run")
    def test_check_pr_exists_success(self, mock_subprocess_run):
        """Test check_pr_exists when PR exists."""
        mock_subprocess_run.return_value = Mock(stdout="789\n")

        from automation.dagster_dev.commands.ai_review_analyze import check_pr_exists

        result = check_pr_exists()
        assert result == "789"

    @patch("subprocess.run")
    def test_check_pr_exists_unexpected_error(self, mock_subprocess_run):
        """Test check_pr_exists with unexpected error."""
        # Simulate unexpected error (not exit code 1)
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            2, "gh", stderr="auth error"
        )

        from automation.dagster_dev.commands.ai_review_analyze import check_pr_exists

        with pytest.raises(subprocess.CalledProcessError):
            check_pr_exists()

    def test_find_previous_branch_found(self):
        """Test find_previous_branch when previous branch exists."""
        all_branches = [
            {"name": "feature", "is_current": True},
            {"name": "main", "is_current": False},
        ]

        from automation.dagster_dev.commands.ai_review_analyze import find_previous_branch

        result = find_previous_branch(all_branches, "feature")
        assert result == "main"

    def test_find_previous_branch_not_found(self):
        """Test find_previous_branch when no previous branch."""
        all_branches = [{"name": "main", "is_current": True}]

        from automation.dagster_dev.commands.ai_review_analyze import find_previous_branch

        result = find_previous_branch(all_branches, "main")
        assert result is None

    def test_find_previous_branch_current_not_found(self):
        """Test find_previous_branch when current branch not found."""
        all_branches = [{"name": "other", "is_current": False}]

        from automation.dagster_dev.commands.ai_review_analyze import find_previous_branch

        result = find_previous_branch(all_branches, "missing")
        assert result is None


class TestAiReviewUpdateComprehensive:
    """Comprehensive tests for ai-review-update targeting 80% coverage."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        assert update_pr is not None
        assert update_pr.name == "ai-review-update"
        assert callable(update_pr)

    def test_help_command(self):
        """Test that help command works and contains expected content."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        runner = CliRunner()
        result = runner.invoke(update_pr, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-update" in result.output
        assert "--title" in result.output
        assert "--body" in result.output
        assert "--auto-prepare" in result.output

    def test_required_parameters(self):
        """Test that title and body parameters are required."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        runner = CliRunner()

        # Missing title
        result = runner.invoke(update_pr, ["--body", "test body"])
        assert result.exit_code != 0
        assert "Missing option '--title'" in result.output

        # Missing body
        result = runner.invoke(update_pr, ["--title", "test title"])
        assert result.exit_code != 0
        assert "Missing option '--body'" in result.output

    def test_command_structure_basic(self):
        """Test basic command structure without execution."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        # Just test that command structure is valid
        assert hasattr(update_pr, "params")
        param_names = [p.name for p in update_pr.params]
        assert "title" in param_names
        assert "body" in param_names
        assert "auto_prepare" in param_names

    @patch("subprocess.run")
    def test_get_pr_number_success(self, mock_subprocess):
        """Test get_pr_number when PR exists."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="123")

        from automation.dagster_dev.commands.ai_review_update import get_pr_number

        result = get_pr_number()
        assert result == "123"

    @patch("subprocess.run")
    def test_get_pr_number_no_pr(self, mock_subprocess):
        """Test get_pr_number when no PR exists."""
        mock_subprocess.return_value = Mock(returncode=1, stdout="")

        from automation.dagster_dev.commands.ai_review_update import get_pr_number

        runner = CliRunner()
        with runner.isolated_filesystem():
            with pytest.raises(SystemExit):
                get_pr_number()

    def test_command_structure_validation(self):
        """Test basic command structure without complex mocking."""
        from automation.dagster_dev.commands.ai_review_update import update_pr

        # Test that command validates required parameters
        runner = CliRunner()
        result = runner.invoke(update_pr, [])

        assert result.exit_code != 0
        assert "--title" in result.output or "--body" in result.output

    def test_run_command_optional_success(self):
        """Test run_command_optional with successful command."""
        with patch("subprocess.run") as mock_subprocess:
            completed_process = subprocess.CompletedProcess(
                args=["echo", "test"], returncode=0, stdout="success", stderr=""
            )
            mock_subprocess.return_value = completed_process

            from automation.dagster_dev.commands.ai_review_update import run_command_optional

            result = run_command_optional(["echo", "test"], "testing")
            assert result.success is True
            assert result.error_message is None

    def test_run_command_optional_failure(self):
        """Test run_command_optional with failed command."""
        with patch("subprocess.run") as mock_subprocess:
            error = subprocess.CalledProcessError(1, "cmd")
            error.stdout = "out"
            error.stderr = "err"
            mock_subprocess.side_effect = error

            from automation.dagster_dev.commands.ai_review_update import run_command_optional

            result = run_command_optional(["false"], "testing failure")
            assert result.success is False
            assert result.error_message is not None
            assert "Error testing failure" in result.error_message
