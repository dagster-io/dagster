"""Simple smoke tests for ai-review-analyze command."""

from click.testing import CliRunner


class TestAiReviewAnalyze:
    """Basic smoke tests for the ai-review-analyze command."""

    def test_import_and_basic_structure(self):
        """Test that command can be imported and has expected structure."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        assert ai_review_analyze is not None
        assert ai_review_analyze.name == "ai-review-analyze"
        assert callable(ai_review_analyze)

    def test_help_command(self):
        """Test that help command works."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--help"])

        assert result.exit_code == 0
        assert "ai-review-analyze" in result.output
        assert "--output" in result.output

    def test_missing_output_parameter(self):
        """Test that output parameter is required."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, [])

        assert result.exit_code != 0
        assert "Missing option '--output'" in result.output
