"""Simple smoke tests for ai-review-summarize command."""

from unittest.mock import patch

from click.testing import CliRunner


class TestAiReviewSummarize:
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
            mock_diff.return_value = {
                "summary": "Test summary",
                "confidence": 0.8,
                "change_type": "feature",
                "files_changed": ["test.py"],
            }

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--format", "json"])

            assert result.exit_code == 0
            mock_diff.assert_called_once()
