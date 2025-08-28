"""Smoke tests for ai-review-summarize command."""

from click.testing import CliRunner


class TestAiReviewSummarizeSmoke:
    """Basic smoke tests to ensure command exists and works."""

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

    def test_basic_invocation_with_invalid_range(self):
        """Test command runs and handles invalid diff range gracefully."""
        from automation.dagster_dev.commands.ai_review_summarize import ai_review_summarize
        
        runner = CliRunner()
        # Use an invalid diff range that should fail gracefully
        result = runner.invoke(ai_review_summarize, ["--diff-range", "invalid..range"])
        
        # Should not crash, but may exit with error code
        assert result.exit_code in [0, 1]  # Allow either success or controlled failure