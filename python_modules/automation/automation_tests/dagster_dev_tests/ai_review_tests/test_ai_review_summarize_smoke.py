"""Simple smoke tests for ai-review-summarize command."""

from unittest.mock import patch

from automation.dagster_dev.commands.diff_summarizer import ChangeType, SmartDiffSummary
from click.testing import CliRunner


class TestAiReviewSummarizeSmoke:
    """Basic smoke tests for the ai-review-summarize command."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        assert ai_review_summarize is not None
        assert ai_review_summarize.name == "ai-review-summarize"
        assert callable(ai_review_summarize)

    def test_help_command(self):
        """Test that help command works."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-summarize" in result.output
        assert "--diff-range" in result.output
        assert "--format" in result.output
        assert "--confidence-threshold" in result.output

    def test_basic_json_output(self):
        """Test basic command with mocked diff summary."""
        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary"
        ) as mock_diff:
            mock_diff.return_value = SmartDiffSummary(
                change_category=ChangeType.NEW_FEATURE,
                files_changed=1,
                additions=10,
                deletions=2,
                functions=[],
                classes=[],
                imports=[],
                key_implementation_details="Test details",
                api_changes=[],
                summary_confidence=0.8,
                needs_detailed_review=False,
            )

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--format", "json"])

            assert result.exit_code == 0
            mock_diff.assert_called_once()

    def test_human_format_output(self):
        """Test command with human-readable format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary"
        ) as mock_diff:
            mock_diff.return_value = SmartDiffSummary(
                change_category=ChangeType.BUG_FIX,
                files_changed=2,
                additions=15,
                deletions=5,
                functions=[],
                classes=[],
                imports=[],
                key_implementation_details="Bug fix details",
                api_changes=[],
                summary_confidence=0.9,
                needs_detailed_review=False,
            )

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--format", "human"])

            assert result.exit_code == 0
            mock_diff.assert_called_once()

    def test_invalid_format(self):
        """Test command with invalid format."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_confidence_threshold_parameter(self):
        """Test that confidence threshold parameter is accepted."""
        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary"
        ) as mock_diff:
            mock_diff.return_value = SmartDiffSummary(
                change_category=ChangeType.REFACTOR,
                files_changed=3,
                additions=20,
                deletions=10,
                functions=[],
                classes=[],
                imports=[],
                key_implementation_details="Refactor details",
                api_changes=[],
                summary_confidence=0.5,
                needs_detailed_review=True,
            )

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--confidence-threshold", "0.3"])

            # Should not crash with valid threshold
            assert result.exit_code == 0
            mock_diff.assert_called_once()

    def test_custom_diff_range(self):
        """Test command with custom diff range."""
        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary"
        ) as mock_diff:
            mock_diff.return_value = SmartDiffSummary(
                change_category=ChangeType.TESTS,
                files_changed=1,
                additions=25,
                deletions=0,
                functions=[],
                classes=[],
                imports=[],
                key_implementation_details="Test additions",
                api_changes=[],
                summary_confidence=0.7,
                needs_detailed_review=False,
            )

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--diff-range", "HEAD~2..HEAD"])

            assert result.exit_code == 0
            mock_diff.assert_called_once()
