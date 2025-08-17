"""Simple smoke tests for ai-review-analyze command."""

import tempfile
from unittest.mock import patch

from click.testing import CliRunner


class TestAiReviewAnalyzeSmoke:
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
        assert "--stack-only" in result.output

    def test_missing_output_parameter(self):
        """Test that output parameter is required."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        result = runner.invoke(ai_review_analyze, [])

        assert result.exit_code != 0
        assert "Missing option '--output'" in result.output

    @patch("automation.dagster_dev.commands.ai_review_analyze.subprocess.run")
    def test_subprocess_error_handling(self, mock_run):
        """Test graceful handling of subprocess errors."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, ["test"])

        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
            result = runner.invoke(ai_review_analyze, ["--output", tmp.name])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_valid_flags_accepted(self):
        """Test that valid command flags are accepted."""
        from automation.dagster_dev.commands.ai_review_analyze import ai_review_analyze

        runner = CliRunner()
        # Just test that the flags don't cause argument parsing errors
        result = runner.invoke(ai_review_analyze, ["--help"])

        assert result.exit_code == 0
        # Check that key flags are documented
        assert "--stack-only" in result.output
        assert "--output" in result.output
