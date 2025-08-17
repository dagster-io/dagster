"""Simple smoke tests for ai-review-summarize command."""

from unittest.mock import patch

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

    def test_human_format_output(self):
        """Test command with human-readable format."""
        with patch(
            "automation.dagster_dev.commands.ai_review_summarize.get_smart_diff_summary"
        ) as mock_diff:
            with patch(
                "automation.dagster_dev.commands.ai_review_summarize.format_summary_for_ai"
            ) as mock_format:
                mock_diff.return_value = {"summary": "Test", "confidence": 0.9}
                mock_format.return_value = "Human readable summary"

                from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

                runner = CliRunner()
                result = runner.invoke(ai_review_summarize, ["--format", "human"])

                assert result.exit_code == 0
                mock_format.assert_called_once()

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
            mock_diff.return_value = {"summary": "Test", "confidence": 0.5}

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
            mock_diff.return_value = {"summary": "Test", "confidence": 0.7}

            from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

            runner = CliRunner()
            result = runner.invoke(ai_review_summarize, ["--diff-range", "HEAD~2..HEAD"])

            assert result.exit_code == 0
            mock_diff.assert_called_once()
