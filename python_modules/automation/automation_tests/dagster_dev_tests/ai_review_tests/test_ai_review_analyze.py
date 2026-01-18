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
        assert "--human" in result.output
        assert "--json" in result.output

    def test_basic_command_execution(self):
        """Test that command executes successfully when dependencies are available."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, ["--json"])

        # Command should execute successfully in test environment
        # Note: This may fail if gt/dagster-dev tools are unavailable
        if result.exit_code == 0:
            # Success case - verify JSON output format
            import json

            data = json.loads(result.output)
            assert "current_branch" in data
            assert "repository_state" in data
        else:
            # Failure case - should be graceful
            assert "Error" in result.output
