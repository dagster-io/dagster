"""Simple smoke tests for ai-review-summarize command."""

from click.testing import CliRunner


class TestAiReviewSummarizeSmoke:
    """Basic smoke tests for the ai-review-summarize command."""

    def test_command_exists(self):
        """Test that the command can be imported."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        assert ai_review_summarize is not None
        assert callable(ai_review_summarize)

    def test_help_shows(self):
        """Test that help command runs without error."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-summarize" in result.output

    def test_invalid_format_fails(self):
        """Test command gracefully handles invalid format."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize

        runner = CliRunner()
        result = runner.invoke(ai_review_summarize, ["--format", "invalid"])

        assert result.exit_code != 0
